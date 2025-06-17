# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import contextvars
import functools
import inspect
import io
import json
import logging
import random
import re
import string
import sys

import flask

from werkzeug.local import LocalProxy

_EXECUTION_ID_LENGTH = 12
_EXECUTION_ID_CHARSET = string.digits + string.ascii_letters
_LOGGING_API_LABELS_FIELD = "logging.googleapis.com/labels"
_LOGGING_API_SPAN_ID_FIELD = "logging.googleapis.com/spanId"
_TRACE_CONTEXT_REGEX_PATTERN = re.compile(
    r"^(?P<trace_id>[\w\d]+)/(?P<span_id>\d+);o=(?P<options>[01])$"
)
EXECUTION_ID_REQUEST_HEADER = "Function-Execution-Id"
TRACE_CONTEXT_REQUEST_HEADER = "X-Cloud-Trace-Context"

logger = logging.getLogger(__name__)

# Context variable for async execution context
execution_context_var = contextvars.ContextVar("execution_context", default=None)


class ExecutionContext:
    def __init__(self, execution_id=None, span_id=None):
        self.execution_id = execution_id
        self.span_id = span_id


def _get_current_context():
    context = execution_context_var.get()
    if context is not None:
        return context
    return (  # pragma: no cover
        flask.g.execution_id_context
        if flask.has_request_context() and "execution_id_context" in flask.g
        else None
    )


def _set_current_context(context):
    execution_context_var.set(context)
    # Also set in Flask context if available for sync
    if flask.has_request_context():
        flask.g.execution_id_context = context


def _generate_execution_id():
    return "".join(
        _EXECUTION_ID_CHARSET[random.randrange(len(_EXECUTION_ID_CHARSET))]
        for _ in range(_EXECUTION_ID_LENGTH)
    )


def _extract_context_from_headers(headers):
    """Extract execution context from request headers."""
    trace_context = re.match(
        _TRACE_CONTEXT_REGEX_PATTERN,
        headers.get(TRACE_CONTEXT_REQUEST_HEADER, ""),
    )
    execution_id = headers.get(EXECUTION_ID_REQUEST_HEADER)
    span_id = trace_context.group("span_id") if trace_context else None

    return ExecutionContext(execution_id, span_id)


# Middleware to add execution id to request header if one does not already exist
class WsgiMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        execution_id = (
            environ.get("HTTP_FUNCTION_EXECUTION_ID") or _generate_execution_id()
        )
        environ["HTTP_FUNCTION_EXECUTION_ID"] = execution_id
        return self.wsgi_app(environ, start_response)


class AsgiMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":  # pragma: no branch
            execution_id_header = b"function-execution-id"
            execution_id = None

            for name, value in scope.get("headers", []):
                if name.lower() == execution_id_header:
                    execution_id = value.decode("latin-1")
                    break

            if not execution_id:
                execution_id = _generate_execution_id()
                new_headers = list(scope.get("headers", []))
                new_headers.append(
                    (execution_id_header, execution_id.encode("latin-1"))
                )
                scope["headers"] = new_headers

        await self.app(scope, receive, send)


def set_execution_context(request, enable_id_logging=False):
    """Decorator for Flask/WSGI handlers that sets execution context.

    Takes request object at decoration time (Flask pattern where request is available
    via thread-local context when decorator is applied).

    Usage:
        @set_execution_context(request, enable_id_logging=True)
        def view_func(path):
            ...
    """
    if enable_id_logging:
        stdout_redirect = contextlib.redirect_stdout(
            LoggingHandlerAddExecutionId(sys.stdout)
        )
        stderr_redirect = contextlib.redirect_stderr(
            LoggingHandlerAddExecutionId(sys.stderr)
        )
    else:
        stdout_redirect = contextlib.nullcontext()
        stderr_redirect = contextlib.nullcontext()

    def decorator(view_function):
        @functools.wraps(view_function)
        def wrapper(*args, **kwargs):
            context = _extract_context_from_headers(request.headers)
            _set_current_context(context)

            with stderr_redirect, stdout_redirect:
                result = view_function(*args, **kwargs)
                return result

        return wrapper

    return decorator


def set_execution_context_async(enable_id_logging=False):
    """Decorator for ASGI/async handlers that sets execution context.

    Unlike set_execution_context which takes request at decoration time (Flask pattern),
    this expects the decorated function to receive request as its first parameter (ASGI pattern).

    Usage:
        @set_execution_context_async(enable_id_logging=True)
        async def handler(request, *args, **kwargs):
            ...
    """
    if enable_id_logging:
        stdout_redirect = contextlib.redirect_stdout(
            LoggingHandlerAddExecutionId(sys.stdout)
        )
        stderr_redirect = contextlib.redirect_stderr(
            LoggingHandlerAddExecutionId(sys.stderr)
        )
    else:
        stdout_redirect = contextlib.nullcontext()
        stderr_redirect = contextlib.nullcontext()

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(request, *args, **kwargs):
            context = _extract_context_from_headers(request.headers)
            token = execution_context_var.set(context)

            with stderr_redirect, stdout_redirect:
                result = await func(request, *args, **kwargs)

                execution_context_var.reset(token)
                return result

        @functools.wraps(func)
        def sync_wrapper(request, *args, **kwargs):
            context = _extract_context_from_headers(request.headers)
            token = execution_context_var.set(context)

            with stderr_redirect, stdout_redirect:
                result = func(request, *args, **kwargs)

                execution_context_var.reset(token)
                return result

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@LocalProxy
def logging_stream():
    return LoggingHandlerAddExecutionId(stream=flask.logging.wsgi_errors_stream)


class LoggingHandlerAddExecutionId(io.TextIOWrapper):
    def __new__(cls, stream=sys.stdout):
        if isinstance(stream, LoggingHandlerAddExecutionId):
            return stream
        else:
            return super(LoggingHandlerAddExecutionId, cls).__new__(cls)

    def __init__(self, stream=sys.stdout):
        io.TextIOWrapper.__init__(self, io.StringIO())
        self.stream = stream

    def write(self, contents):
        if contents == "\n":
            return
        current_context = _get_current_context()
        if current_context is None:
            self.stream.write(contents + "\n")
            self.stream.flush()
            return
        try:
            execution_id = current_context.execution_id
            span_id = current_context.span_id
            payload = json.loads(contents)
            if not isinstance(payload, dict):
                payload = {"message": contents}
        except json.JSONDecodeError:
            if len(contents) > 0 and contents[-1] == "\n":
                contents = contents[:-1]
            payload = {"message": contents}
        if execution_id:
            payload[_LOGGING_API_LABELS_FIELD] = payload.get(
                _LOGGING_API_LABELS_FIELD, {}
            )
            payload[_LOGGING_API_LABELS_FIELD]["execution_id"] = execution_id
        if span_id:
            payload[_LOGGING_API_SPAN_ID_FIELD] = span_id
        self.stream.write(json.dumps(payload))
        self.stream.write("\n")
        self.stream.flush()
