"""Monitoring - Structured logging and OpenTelemetry tracing"""
import logging
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict


# ------- Structured JSON Logging -------

class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Merge any extra fields passed via extra={}
        for key, value in record.__dict__.items():
            if key not in (
                "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "name", "message"
            ):
                log_data[key] = value

        return json.dumps(log_data, default=str)


def configure_logging(level: str = "INFO", json_format: bool = True) -> None:
    """Configure application logging"""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
        ))

    root_logger.handlers = [handler]

    # Silence noisy third-party loggers
    for noisy in ["sqlalchemy.engine", "httpx", "httpcore", "uvicorn.access"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ------- OpenTelemetry Tracing -------

def configure_tracing(service_name: str = "chatbot-backend") -> None:
    """Configure OpenTelemetry tracing if packages are available"""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)

        FastAPIInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()

        logging.getLogger(__name__).info(
            "OpenTelemetry tracing configured",
            extra={"service_name": service_name, "otlp_endpoint": otlp_endpoint}
        )

    except ImportError:
        logging.getLogger(__name__).warning(
            "OpenTelemetry packages not installed — tracing disabled"
        )


# ------- Prometheus metrics -------

def get_prometheus_instrumentator():
    """Return prometheus instrumentator if available"""
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        return Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_group_untemplated=True,
            excluded_handlers=["/health", "/metrics"],
        )
    except ImportError:
        return None
