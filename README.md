# service-shortlink

| Branch  | Status                                                                                                                                                                                                                                                                                                                      |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| develop | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiOGt4dm5YZ05Yd2NGQmlIS01qSEZHQkFGV1UxblFyc0owY1dvek9MdUM4dWE1LzIwdTJ1WTB3WExHQ0RrK1d3WmY1M0FPUlJueUxyN3FTRlNpdjBaY2Y0PSIsIml2UGFyYW1ldGVyU3BlYyI6Ild2aS9qL0k3U1VzSVRsdGkiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=develop) |
| master  | ![Build Status](https://codebuild.eu-central-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiOGt4dm5YZ05Yd2NGQmlIS01qSEZHQkFGV1UxblFyc0owY1dvek9MdUM4dWE1LzIwdTJ1WTB3WExHQ0RrK1d3WmY1M0FPUlJueUxyN3FTRlNpdjBaY2Y0PSIsIml2UGFyYW1ldGVyU3BlYyI6Ild2aS9qL0k3U1VzSVRsdGkiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)  |

## Table of content

- [Description](#description)
- [Dependencies](#dependencies)
- [Service API](#service-api)
- [Local Development](#local-development)
- [Docker helpers](#docker-helpers)
- [Versioning](#versioning)
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

| Environment | URL                                                      |
| ----------- | -------------------------------------------------------- |
| DEV         | [https://sys-s.dev.bgdi.ch/](https://sys-s.dev.bgdi.ch/) |
| INT         | [https://sys-s.int.bgdi.ch/](https://sys-s.int.bgdi.ch/) |
| PROD        | [https://s.geo.admin.ch/](https://s.geo.admin.ch/)       |

### Checker GET

This is a simple route meant to test if the server is up.

| Path     | Method | Argument | Response Type    |
| -------- | ------ | -------- | ---------------- |
| /checker | GET    | None     | application/json |


### Shortlink Creation POST

This route takes a json containing an url as a payload. It checks if the hostname and domain are part of the allowed names and domains,
then create a shortened url that is stored in a dynamodb database. If the given url already exists, within dynamodb, it returns
the already existing shortened url instead.


| Path | Method | Argument | Content Type     | Content                              | Response Type    |
| ---- | ------ | -------- | ---------------- | ------------------------------------ | ---------------- |
| /    | POST   | None     | application/json | `{"url": "https://map.geo.admin.ch}` | application/json |

### URL recuperation GET

This routes search the database for the given ID and returns a json containing the corresponding url if found.
The redirect parameter redirect the user to the corresponding url instead if set to true.

| Path             | Method | Argument                              | Response Type                   |
| ---------------- | ------ | ------------------------------------- | ------------------------------- |
| /<shortlinks_id> | GET    | optional : redirect ('true', 'false') | application/json or redirection |

## Local Development

### Dependencies

The **Make** targets assume you have **bash**, **curl**, **tar**, **docker** and **docker-compose-plugin** installed.

### Setting up to work

First, you'll need to clone the repo

    git clone git@github.com:geoadmin/service-name

Then, you can run the setup target to ensure you have everything needed to develop, test and serve locally

    make setup

The other service that is used (DynamoDB local) is wrapped in a docker compose. Starting DynamoDB local is done with a simple

    docker compose up

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

For testing the locally served application with the commands below, be sure to set
ENV_FILE to .env.default and start a local DynamoDB image beforehand with:

    docker compose up &
    export ENV_FILE=.env.default

The following three make targets will serve the application locally:

    make serve

This will serve the application through Flask without any wsgi in front.

    make gunicornserve

This will serve the application with the Gunicorn layer in front of the application

    make dockerrun

This will serve the application with the wsgi server, inside a container.

To stop serving through containers,

    make shutdown

Is the command you're looking for.

A curl example for testing the generation of shortlinks on the local db is:

    curl -X POST -H "Content-Type: application/json" -H "Origin: https://map.geo.admin.ch" -d '{"url":"https://map.geo.admin.ch"}' http://localhost:5000

### Docker helpers

From each github PR that is merged into `master` or into `develop`, one Docker image is built and pushed on AWS ECR with the following tag:

- `vX.X.X` for tags on master
- `vX.X.X-beta.X` for tags on develop

Each image contains the following metadata:

- author
- git.branch
- git.hash
- git.dirty
- version

These metadata can be read with the following command

```bash
make dockerlogin
docker pull 974517877189.dkr.ecr.eu-central-1.amazonaws.com/service-shortcut:develop.latest

# NOTE: jq is only used for pretty printing the json output,
# you can install it with `apt install jq` or simply enter the command without it
docker image inspect --format='{{json .Config.Labels}}' 974517877189.dkr.ecr.eu-central-1.amazonaws.com/service-shortcut:develop.latest | jq
```

You can also check these metadata on a running container as follows

```bash
docker ps --format="table {{.ID}}\t{{.Image}}\t{{.Labels}}"
```

To build a local docker image tagged as `service-shortcut:local-${USER}-${GIT_HASH_SHORT}` you can
use

```bash
make dockerbuild
```

To push the image on the ECR repository use the following two commands

```bash
make dockerlogin
make dockerpush
```


## Deployment

When creating a PR, terraform should run a codebuild job to test, build and push automatically your PR as a tagged container.

This service is to be delployed to the Kubernetes cluster once it is merged.

### Deployment Configuration

The service is configured by Environment Variable:

| Env Variable                  | Default                                   | Description                                                                                                                                                                      |
| ----------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LOGGING_CFG                   | `logging-cfg-local.yml`                   | Logging configuration file to use.                                                                                                                                               |
| AWS_ACCESS_KEY_ID             |                                           | Necessary credential to access dynamodb                                                                                                                                          |
| AWS_SECRET_ACCESS_KEY         |                                           | AWS_SECRET_ACCESS_KEY                                                                                                                                                            |
| AWS_DYNAMODB_TABLE_NAME       |                                           | The dynamodb table name                                                                                                                                                          |
| AWS_DEFAULT_REGION            | eu-central-1                              | The AWS region in which the table is hosted.                                                                                                                                     |
| AWS_ENDPOINT_URL              |                                           | The AWS endpoint url to use                                                                                                                                                      |
| ALLOWED_DOMAINS               | `.*`                                      | A comma separated list of allowed domains names                                                                                                                                  |
| FORWARED_ALLOW_IPS            | `*`                                       | Sets the gunicorn `forwarded_allow_ips` (see https://docs.gunicorn.org/en/stable/settings.html#forwarded-allow-ips). This is required in order to `secure_scheme_headers` works. |
| FORWARDED_PROTO_HEADER_NAME   | `X-Forwarded-Proto`                       | Sets gunicorn `secure_scheme_headers` parameter to `{FORWARDED_PROTO_HEADER_NAME: 'https'}`, see https://docs.gunicorn.org/en/stable/settings.html#secure-scheme-headers.        |
| CACHE_CONTROL                 | `public, max-age=31536000`                | Cache Control header value of the `GET /<shortlink>` endpoint                                                                                                                    |
| CACHE_CONTROL_4XX             | `public, max-age=3600`                    | Cache Control header for 4XX responses                                                                                                                                           |
| GUNICORN_KEEPALIVE            | `2`                                       | The [`keepalive`](https://docs.gunicorn.org/en/stable/settings.html#keepalive) setting passed to gunicorn.                                                                       |
| GUNICORN_WORKER_TMP_DIR       |                                           | This should be set to an tmpfs file system for better performance. See https://docs.gunicorn.org/en/stable/settings.html#worker-tmp-dir.                                         |
| SHORT_ID_SIZE                 | `12`                                      | The size (number of characters) of the shortloink id's                                                                                                                           |
| SHORT_ID_ALPHABET             | `0123456789abcdefghijklmnopqrstuvwxyz`    | The alphabet (characters) used by the shortlink. Allowed chars `[0-9][A-Z][a-z]-_`                                                                                               |

## OTEL

[OpenTelemetry instrumentation](https://opentelemetry.io/docs/concepts/instrumentation/) can be done in many different ways, from fully automated zero-code instrumentation (otel-operator) to purely manual instrumentation.
We use the so called `OTEL programmatical instrumentation` approach where we import the specific instrumentation libraries and initialize them with the instrument() method of each library.

### Environment variables

The following env variables can be used to configure OTEL

| Env Variable                                              | Default                    | Description                                                                                                                                          |
| --------------------------------------------------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| OTEL_SDK_DISABLED                                         | false                      | If set to "true", OTEL is disabled. See: https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/#general-sdk-configuration |
| OTEL_ENABLE_BOTO                                          | false                      | If opentelemetry-instrumentation-botocore should be enabled or not.                                                                                  |
| OTEL_ENABLE_FLASK                                         | false                      | If opentelemetry-instrumentation-django should be enabled or not.                                                                                    |
| OTEL_ENABLE_LOGGING                                       | false                      | If opentelemetry-instrumentation-logging should be enabled or not.                                                                                   |
| OTEL_EXPERIMENTAL_RESOURCE_DETECTORS                      |                            | OTEL resource detectors, adding resource attributes to the OTEL output. e.g. `os,process`                                                            |
| OTEL_EXPORTER_OTLP_ENDPOINT                               | http://localhost:4317      | The OTEL Exporter endpoint, e.g. `opentelemetry-kube-stack-gateway-collector.opentelemetry-operator-system:4317`                                     |
| OTEL_EXPORTER_OTLP_HEADERS                                |                            | A list of key=value headers added in outgoing data. https://opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/#header-configuration    |
| OTEL_EXPORTER_OTLP_INSECURE                               | false                      | If exporter ssl certificates should be checked or not.                                                                                               |
| OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST  |                            | A comma separated list of request headers added in outgoing data. Regex supported. Use '.*' for all headers                                          |
| OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE |                            | A comma separated list of request headers added in outgoing data. Regex supported. Use '.*' for all headers                                          |
| OTEL_PYTHON_FLASK_EXCLUDED_URLS                           |                            | A comma separated list of url's to exclude, e.g. `checker`                                                                                           |
| OTEL_RESOURCE_ATTRIBUTES                                  |                            | A comma separated list of custom OTEL resource attributes, Must contain at least the service-name `service.name=service-shortlink`                   |
| OTEL_TRACES_SAMPLER                                       | parentbased_always_on      | Sampler to be used, see https://opentelemetry-python.readthedocs.io/en/latest/sdk/trace.sampling.html#module-opentelemetry.sdk.trace.sampling.       |
| OTEL_TRACES_SAMPLER_ARG                                   |                            | Optional additional arguments for sampler.                                                                                                           |
| OTEL_TRACES_SAMPLER                                       | parentbased_always_on      | Sampler to be used, see https://opentelemetry-python.readthedocs.io/en/latest/sdk/trace.sampling.html#module-opentelemetry.sdk.trace.sampling.       |
| OTEL_TRACES_SAMPLER_ARG                                   |                            | Optional additional arguments for sampler.                                                                                                           |

### Adding a New Instrumentation

1. Use `edot-bootstrap --action=requirements` to get a list of possible instrumentation libraries
2. Add all or the desired ones to the Pipfile.
3. Add the initalization to [otel.py](app/helpers/otel.py) together with a feature flag

Note: `edot-bootstrap` should be already installed via `infra-ansible-bgdi-dev`. If not, install it with `pipx install elastic-opentelemetry`.

### Log Correlation

The OpenTelemetry logging integration automatically injects tracing context into log statements. The following keys are injected into log record objects:

- otelSpanID
- otelTraceID
- otelTraceSampled

Note that although otelServiceName is injected, it will be empty. This is because the logging integration tries to read the service name from the trace provider, but our trace provider instance does not contain this resource attribute.

### Sampling

The python SDK supports ratio based [head sampling](https://opentelemetry.io/docs/concepts/sampling/#head-sampling). To enable, set

- OTEL_TRACES_SAMPLER=parentbased_traceidratio|traceidratio
- and OTEL_TRACES_SAMPLER_ARG=[0.0,1.0]

### Local Telemetry

Local telemetry can be tested by using one of the serve commands that use gunicorn, either `make gunicornserve`  or `make dockerrun`, and visiting the Zipkin dashboard at [http://localhost:9411](http://localhost:9411).
