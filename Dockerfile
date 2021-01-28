# Buster slim python 3.7 base image.
FROM python:3.7-slim-buster
ENV HTTP_PORT 8080
RUN groupadd -r geoadmin && useradd -r -s /bin/false -g geoadmin geoadmin


# HERE : install relevant packages
# RUN apt-get update && apt-get install -y [packages] \
#  && apt-get clean \
#  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY "./requirements.txt" "/app/requirements.txt"

RUN pip3 install -r requirements.txt

COPY "./" "/app/"


ARG GIT_HASH=unknown
ARG GIT_BRANCH=unknown
ARG GIT_DIRTY=""
ARG VERSION=unknown
ARG AUTHOR=unknown
LABEL git.hash=$GIT_HASH
LABEL git.branch=$GIT_BRANCH
LABEL git.dirty="$GIT_DIRTY"
LABEL version=$VERSION
LABEL author=$AUTHOR

# Overwrite the version.py from source with the actual version
RUN echo "APP_VERSION = '$VERSION'" > /app/app/version.py

RUN chown -R geoadmin:geoadmin /app
USER geoadmin

EXPOSE $HTTP_PORT

# Use a real WSGI server
ENTRYPOINT ["python3", "wsgi.py"]
