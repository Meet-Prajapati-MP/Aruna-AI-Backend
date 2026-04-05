"""
app/utils/logger.py
────────────────────
Structured JSON logging via structlog.
In production every log line is a JSON object — easy to ingest
into Datadog, Logtail, or Railway's log viewer.
"""

import logging
import sys

import structlog


def configure_logging(is_production: bool = False) -> None:
    # Route stdlib logging to stdout so structlog output appears in Railway logs.
    # Must be called before structlog.configure() so the handler is in place.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG,
        force=True,  # replace any handlers already attached by uvicorn
    )

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,   # requires stdlib logger (.name attr)
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_production:
        # JSON output for log aggregators (Railway, Datadog, Logtail …)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable output; disable ANSI colours outside a real TTY
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty()),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        # stdlib.LoggerFactory() creates loggers backed by Python's logging
        # module — they have the .name attribute that add_logger_name needs.
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    return structlog.get_logger(name)
