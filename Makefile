SHELL = /bin/bash

.DEFAULT_GOAL := help

SERVICE_NAME := service-shortlink

CURRENT_DIR := $(shell pwd)
INSTALL_DIR := $(shell pipenv --venv)
PYTHON_FILES := $(shell find ./* -type f -name "*.py" -print)
TEST_REPORT_DIR := $(CURRENT_DIR)/tests/report
TEST_REPORT_FILE := nose2-junit.xml
LOGS_DIR = $(PWD)/logs

# PIPENV files
PIP_FILE = Pipfile
PIP_FILE_LOCK = Pipfile.lock

# default configuration
HTTP_PORT ?= 5000

# Commands

PIPENV_RUN := pipenv run
PYTHON_CMD := $(PIPENV_RUN) python3
PIP_CMD := $(PIPENV_RUN) pip3
FLASK_CMD := $(PIPENV_RUN) flask
YAPF_CMD := $(PIPENV_RUN) yapf
ISORT_CMD := $(PIPENV_RUN) isort
NOSE_CMD := $(PIPENV_RUN) nose2
PYLINT_CMD := $(PIPENV_RUN) pylint
EDOT_BOOTSTRAP_CMD := $(PIPENV_RUN) edot-bootstrap

# AWS variables
AWS_DEFAULT_REGION = eu-central-1

# Docker metadata
GIT_HASH := `git rev-parse HEAD`
GIT_HASH_SHORT = `git rev-parse --short HEAD`
GIT_BRANCH := `git symbolic-ref HEAD --short 2>/dev/null`
GIT_DIRTY := `git status --porcelain`
GIT_TAG := `git describe --tags || echo "no version info"`
AUTHOR := $(USER)

# Docker variables
DOCKER_REGISTRY = 974517877189.dkr.ecr.eu-central-1.amazonaws.com
DOCKER_IMG_LOCAL_TAG = $(DOCKER_REGISTRY)/$(SERVICE_NAME):local-$(USER)-$(GIT_HASH_SHORT)

all: help

# This bit check define the build/python "target": if the system has an acceptable version of python, there will be no need to install python locally.


.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@echo -e " \033[1mBUILD TARGETS\033[0m "
	@echo "- setup              Create the python virtual environment with developper tools and activate it"
	@echo "- ci                 Create the python virtual environment and install requirements based on the Pipfile.lock"
	@echo -e " \033[1mFORMATING, LINTING AND TESTING TOOLS TARGETS\033[0m "
	@echo "- format             Format the python source code"
	@echo "- lint               Lint the python source code"
	@echo "- format-lint        Format and lint the python source code"
	@echo "- test               Run the tests"
	@echo -e " \033[1mLOCAL SERVER TARGETS\033[0m "
	@echo "- serve              Run the project using the flask debug server"
	@echo "- gunicornserve      Run the project using the gunicorn WSGI server"
	@echo "- dockerlogin        Login to the AWS ECR registery for pulling/pushing docker images"
	@echo "- dockerbuild        Build the project localy using the gunicorn WSGI server inside a container"
	@echo "- dockerpush         Build and push the project localy (with tag := $(DOCKER_IMG_LOCAL_TAG))"
	@echo "- dockerrun          Run the project using the gunicorn WSGI server inside a container. (Exposed_port: $(HTTP_PORT)"
	@echo "- shutdown           Stop the aforementioned container"
	@echo -e " \033[1mCLEANING TARGETS\033[0m "
	@echo "- clean              Clean genereated files"
	@echo "- clean_venv         Clean python venv"
	@echo "- clean_logs         Clean logs"


# Build targets. Calling setup is all that is needed for the local files to be installed as needed.

.PHONY: setup
setup:
	pipenv install --dev
	pipenv shell

.PHONY: ci
ci:
	# Create virtual env with all packages for development using the Pipfile.lock
	pipenv sync --dev

# linting target, calls upon yapf to make sure your code is easier to read and respects some conventions.

.PHONY: format
format:
	$(YAPF_CMD) -p -i --style .style.yapf $(PYTHON_FILES)
	$(ISORT_CMD) $(PYTHON_FILES)

.PHONY: ci-check-format
ci-check-format: format
	@if [[ -n `git status --porcelain` ]]; then \
	 	>&2 echo "ERROR: the following files are not formatted correctly:"; \
		>&2 git status --porcelain; \
		exit 1; \
	fi

.PHONY: lint
lint:
	$(PYLINT_CMD) $(PYTHON_FILES)


.PHONY: format-lint
format-lint: format lint


.PHONY: test
test:
	mkdir -p $(TEST_REPORT_DIR)
	ENV_FILE=.env.testing $(NOSE_CMD) -c tests/unittest.cfg -v --junit-xml-path $(TEST_REPORT_DIR)/$(TEST_REPORT_FILE) -s tests/

# Serve targets. Using these will run the application on your local machine. You can either serve with a wsgi front (like it would be within the container), or without.
.PHONY: serve
serve: clean_logs $(LOGS_DIR)
	ENV_FILE=.env.default LOGS_DIR=$(LOGS_DIR) FLASK_APP=service_launcher FLASK_DEBUG=1 $(FLASK_CMD) run --host=0.0.0.0 --port=$(HTTP_PORT)

.PHONY: gunicornserve
gunicornserve: clean_logs $(LOGS_DIR)
	ENV_FILE=.env.default LOGS_DIR=$(LOGS_DIR) ${PYTHON_CMD} wsgi.py

# Docker related functions.
.PHONY: dockerlogin
dockerlogin:
	aws --profile swisstopo-bgdi-builder ecr get-login-password --region $(AWS_DEFAULT_REGION) | docker login --username AWS --password-stdin $(DOCKER_REGISTRY)

.PHONY: dockerbuild
dockerbuild:
	docker build \
		--build-arg GIT_HASH="$(GIT_HASH)" \
		--build-arg GIT_BRANCH="$(GIT_BRANCH)" \
		--build-arg GIT_DIRTY="$(GIT_DIRTY)" \
		--build-arg VERSION="$(GIT_TAG)" \
		--build-arg HTTP_PORT="$(HTTP_PORT)" \
		--build-arg AUTHOR="$(AUTHOR)" \
		-t $(DOCKER_IMG_LOCAL_TAG) .

.PHONY: dockerpush
dockerpush: dockerbuild
	docker push $(DOCKER_IMG_LOCAL_TAG)


.PHONY: dockerrun
dockerrun: clean_logs dockerbuild $(LOGS_DIR)
	docker run \
		-it \
		--network=host \
		--env-file=.env.default \
		--env LOGS_DIR=/logs \
		--mount type=bind,source="${LOGS_DIR}",target=/logs \
		$(DOCKER_IMG_LOCAL_TAG)


# Cleaning functions. clean_venv will only remove the virtual environment, while clean will also remove the local python installation.

.PHONY: clean_venv
clean_venv:
	pipenv --rm


.PHONY: clean_logs
clean_logs:
	rm -rf $(LOGS_DIR)


.PHONY: clean
clean: clean_venv clean_logs
	@# clean python cache files
	find . -name __pycache__ -type d -print0 | xargs -I {} -0 rm -rf "{}"
	rm -rf $(TEST_REPORT_DIR)

# Actual builds targets with dependencies

$(LOGS_DIR):
	mkdir -p -m=777 $(LOGS_DIR)
