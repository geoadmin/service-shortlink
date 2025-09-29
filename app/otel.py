# https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/flask/flask.html
# https://www.elastic.co/observability-labs/blog/manual-instrumentation-python-apps-opentelemetry
# https://github.com/aws-observability/aws-otel-community/blob/master/sample-apps/python-manual-instrumentation-sample-app/app.py
import os
import platform

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.app import app
from app.helpers import utils


def read_file(path, default="unknown"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return default


def get_resource_attributes():
    attributes = {}
    # Note: Add only the parameters which are needed and can not be automatically
    # retrieved by pipeline components like OTEL collectors.

    # Needed by otel collector gateway k8sattributes processor to identify
    # pod and automatically enrich with additional fields.
    attributes["k8s.pod.ip"] = os.getenv("K8S_POD_IP", "unknown")
    attributes["k8s.container.name"] = os.getenv("K8S_CONTAINER_NAME", "unknown").lower()

    # Fields which can not be automatically collected by other components
    attributes["service.name"] = os.getenv("SERVICE_NAME", "unknown").lower()
    attributes["os.type"] = platform.system().lower()
    attributes["os.version"] = platform.platform(terse=True).lower()
    attributes["process.runtime.description"] = (
        f"{platform.python_version()} "
        f"({', '.join(platform.python_build())}) [{platform.python_compiler()}]"
    )
    attributes["process.runtime.version"] = platform.python_version()
    attributes["process.runtime.name"] = platform.python_implementation().lower()

    # Add additional attributes if available
    custom_attributes_string = os.environ.get('OTEL_RESOURCE_ATTRIBUTES')
    if custom_attributes_string:
        for pair in custom_attributes_string.split(','):
            key, value = pair.split('=')
            attributes[key] = value

    return attributes


def setup_instrumentation():
    BotocoreInstrumentor().instrument()
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()


def setup_opentelemetry():

    tracer = trace.get_tracer(__name__)

    otel_exporter_otlp_headers = os.getenv('OTEL_EXPORTER_OTLP_HEADERS')
    otel_exporter_otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', "http://localhost:4317")
    otel_exporter_otlp_insecure = os.getenv('OTEL_EXPORTER_OTLP_INSECURE', "false")
    # fail if server url not set
    if otel_exporter_otlp_endpoint is None:
        raise ValueError('OTEL_EXPORTER_OTLP_ENDPOINT environment variable not set')
    span_exporter = OTLPSpanExporter(
        endpoint=otel_exporter_otlp_endpoint,
        headers=otel_exporter_otlp_headers,
        insecure=utils.strtobool(otel_exporter_otlp_insecure)
    )

    resource = Resource.create(get_resource_attributes())

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(span_exporter)
    provider.add_span_processor(processor)

    # Sets the global default tracer provider
    trace.set_tracer_provider(provider)

    return tracer
