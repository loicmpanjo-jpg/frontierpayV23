"""OpenTelemetry Tracing & Metrics"""
import functools
from typing import Callable, Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from app.core.config import settings


# Setup tracer
resource = Resource.create({SERVICE_NAME: "frontierpay-v23"})
tracer_provider = TracerProvider(resource=resource)

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer("frontierpay.tracer")


def traced(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Decorator for tracing function calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.message", str(e))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.message", str(e))
                    raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


import asyncio
