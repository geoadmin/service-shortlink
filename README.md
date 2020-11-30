# service-shortlink

| Branch | Status |
|--------|-----------|
| develop | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiTzlSRlU5eUZIdlQzb2JDTE9FTXdkNmk0L0d5K0pWMjZLbE00NmtWTjdxS1FFdFpsbVM1QWNqRTgrOGNmNUhib0tjZXRSMUtndTE0dmZ5RDY2blB1K0tNPSIsIml2UGFyYW1ldGVyU3BlYyI6InNUUXlKaU9YUkE1Z0tQci8iLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=develop) |
| master | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiTzlSRlU5eUZIdlQzb2JDTE9FTXdkNmk0L0d5K0pWMjZLbE00NmtWTjdxS1FFdFpsbVM1QWNqRTgrOGNmNUhib0tjZXRSMUtndTE0dmZ5RDY2blB1K0tNPSIsIml2UGFyYW1ldGVyU3BlYyI6InNUUXlKaU9YUkE1Z0tQci8iLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master) |

## Table of content

- [Description](#description)
- [Dependencies](#dependencies)
- [Service API](#service-api)
- [Local Development](#local-development)
- [Deployment](#deployment)

## Description

A REST Microservice which creates and returns short urls, using Flask and Gunicorn, with docker containers as a mean of deployment.

## dependencies

This service needs an external dynamodb database.

## Service API

This service has three endpoints : 

- [Checker GET](#checker-get)
- [Shortlink Creation POST](#shortlinks-creation)
- [URL recuperation GET](#url-get)

You can find a more detailed description of the endpoints in the [OpenAPI Spec](openapi.yaml)

### Staging Environments

|Environment | URL |
|------------|-----|
|DEV         |[]()|
|INT         |[]()|
|PROD        |[]()|

### Checker GET

This is a simple route meant to test if the server is up.

| Path | Method | Argument | Response Type |
|------|--------|----------|---------------|
|/v4/shortlinks/checker|GET| None | application/json|


### Shortlink Creation POST

This route takes a json containing an url as a payload. It checks if the hostname and domain are part of the allowed names and domains, 
then create a shortened url that is stored in a dynamodb database. If the given url already exists, within dynamodb, it returns 
the already existing shortened url instead.


| Path | Method | Argument | Content Type | Content | Response Type |
|------|--------|----------|--------------|---------|---------------|
|/v4/shortlinks/shortlinks|POST| None | application/json| `{"url": "https://map.geo.admin.ch}` | application/json |

### URL recuperation GET

This routes search the database for the given ID and returns a json containing the corresponding url if found.
The redirect parameter redirect the user to the corresponding url instead if set to true.

| Path | Method | Argument | Response Type |
|------|--------|----------|---------------|
|v4/shortlinks/shortlinks/<shortlinks_id>|GET| optional : redirect ('true', 'false')| application/json or redirection |

## Local Development

### dependencies

The **Make** targets assume you have **bash**, **curl**, **tar**, **docker** and **docker-compose** installed.

### Setting up to work

First, you'll need to clone the repo

    git clone git@github.com:geoadmin/service-name

Then, you can run the setup target to ensure you have everything needed to develop, test and serve locally

    make setup

That's it, you're ready to work.

### Linting and formatting your work

In order to have a consistent code style the code should be formatted using `yapf`. Also to avoid syntax errors and non
pythonic idioms code, the project uses the `pylint` linter. Both formatting and linter can be manually run using the
following command:

    make lint

**Formatting and linting should be at best integrated inside the IDE, for this look at
[Integrate yapf and pylint into IDE](https://github.com/geoadmin/doc-guidelines/blob/master/PYTHON.md#yapf-and-pylint-ide-integration)**

### Test your work

Testing if what you developed work is made simple. You have four targets at your disposal. **test, serve, gunicornserve, dockerrun**

    make test

This command run the integration and unit tests.

    make serve

This will serve the application through Flask without any wsgi in front.

    make gunicornserve

This will serve the application with the Gunicorn layer in front of the application

    make dockerrun

This will serve the application with the wsgi server, inside a container.
To stop serving through containers,

    make shutdown

Is the command you're looking for.


## Deployment

When creating a PR, terraform should run a codebuild job to test, build and push automatically your PR as a tagged container.

This service is to be delployed to the Kubernetes cluster once it is merged.

### Deployment Configuration

The service is configured by Environment Variable:

| Env Variable | Default               | Description                        |
|--------------|-----------------------|------------------------------------|
| LOGGING_CFG  | logging-cfg-local.yml | Logging configuration file to use. |
| AWS_ACCESS_KEY_ID | None | Necessary credential to access dynamodb        |
| AWS_SECRET_ACCESS_KEY | None | AWS_SECRET_ACCESS_KEY                      |
| AWS_SECURITY_TOKEN | None | AWS_SECURITY_TOKEN                            |
| AWS_SESSION_TOKEN | None | AWS_SESSION_TOKEN                              |
| ALLOWED_DOMAINS | 'admin.ch,swisstopo.ch,bgdi.ch' | A comma separated list of allowed domains names |
| ALLOWED_HOSTS | 'api.geo.admin.ch,api3.geo.admin.ch' | a comma separated list of allowed hostnames |
| AWS_DYNAMODB_TABLE_NAME | 'shorturl' | The dynamodb table name |
| AWS_DYNAMODB_TABLE_REGION | 'eu-central-1' | The AWS region in which the table is hosted. |