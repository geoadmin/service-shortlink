import os
import platform

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.helpers.utils import strtobool


# Create resource attributes dict to be used in otel data
def get_resource_attributes(worker_pid):
    attributes = {}
    # Note: Only add attributes which can not be added via OTEL_RESOURCE_ATTRIBUTES env variable.

    # Platform attributes
    # These attributes provide useful information. Unfortunately the OTEL SDK does not ship them by default.
    # https://github.com/open-telemetry/opentelemetry-python/issues/3916
    # The same applies to OS attributes
    # For now they are added manually.
    attributes["os.type"] = platform.system().lower()
    attributes["os.version"] = platform.platform(terse=True).lower()
    attributes["process.runtime.description"] = (
        f"{platform.python_version()} "
        f"({', '.join(platform.python_build())}) [{platform.python_compiler()}]"
    )
    attributes["process.runtime.version"] = platform.python_version()
    attributes["process.runtime.name"] = platform.python_implementation().lower()

    # Worker PID as described in OTEL examples
    # https://github.com/open-telemetry/opentelemetry-python/blob/main/docs/examples/fork-process-model/flask-gunicorn/gunicorn.conf.py
    attributes["worker.pid"] = worker_pid

    return attributes


def setup_trace_provider(worker_pid):
    # Resources are immutable. Thus if we want to add some custom attributes from within
    # the python project, we need to create a new tracer with a new resource.

    # Note: Attributes are merged with ones set by OTEL_RESOURCE_ATTRIBUTES env variable.
    # https://opentelemetry-python.readthedocs.io/en/latest/sdk/environment_variables.html#envvar-OTEL_RESOURCE_ATTRIBUTES
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create(get_resource_attributes(worker_pid)))
    )

    # Since we replaced the tracer, the default span processor is gone. We need to
    # create a new one using the default OTEL env variables and ad it to the tracer.
    span_processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', "http://localhost:4317"),
            headers=os.getenv('OTEL_EXPORTER_OTLP_HEADERS', ""),
            insecure=strtobool(os.getenv('OTEL_EXPORTER_OTLP_INSECURE', "false"))
        )
    )
    trace.get_tracer_provider().add_span_processor(span_processor)
