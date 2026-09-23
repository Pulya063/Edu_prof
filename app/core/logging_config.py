"""Centralized application logging.

Logs are written both to the console (CMD) and to a rotating file.  The
``log_call`` decorator is available for service functions where entry/exit
logging is useful; request hooks in ``app.main`` cover every HTTP route.
"""
from __future__ import annotations

import functools
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from flask import Flask, g, request

F = TypeVar("F", bound=Callable[..., Any])


def configure_logging() -> None:
    """Configure console and rotating file handlers once per process."""
    root = logging.getLogger()
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

    log_file = Path(os.getenv("LOG_FILE", "app/logs/app.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Avoid duplicate lines when Flask's debug reloader calls create_app twice.
    if not any(getattr(handler, "_education_roi_handler", False) for handler in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        console._education_roi_handler = True  # type: ignore[attr-defined]
        root.addHandler(console)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler._education_roi_handler = True  # type: ignore[attr-defined]
        root.addHandler(file_handler)


def log_call(func: F) -> F:
    """Log service function start, successful completion, and exceptions."""
    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        logger.info("Function %s started", func.__qualname__)
        try:
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info("Function %s finished in %.2f ms", func.__qualname__, elapsed_ms)
            return result
        except Exception:
            logger.exception("Function %s failed", func.__qualname__)
            raise

    return cast(F, wrapper)


def register_request_logging(flask_app: Flask) -> None:
    """Add lifecycle logging for every incoming request and its response."""
    logger = logging.getLogger("app.request")

    @flask_app.before_request
    def log_request_start() -> None:
        g.request_started_at = time.perf_counter()
        logger.info(
            "Request started: %s %s%s user_id=%s",
            request.method,
            request.path,
            f"?{request.query_string.decode('utf-8', errors='replace')}" if request.query_string else "",
            getattr(getattr(g, "user", None), "id", "anonymous"),
        )

    @flask_app.after_request
    def log_request_end(response: Any) -> Any:
        started = getattr(g, "request_started_at", time.perf_counter())
        logger.info(
            "Request finished: %s %s status=%s duration_ms=%.2f",
            request.method,
            request.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
        )
        return response

    @flask_app.teardown_request
    def log_request_exception(error: BaseException | None) -> None:
        if error is not None:
            logger.error(
                "Request failed: %s %s",
                request.method,
                request.path,
                exc_info=(type(error), error, error.__traceback__),
            )
