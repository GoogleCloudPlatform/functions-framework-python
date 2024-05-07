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
import functools
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


class ExecutionContext:
    def __init__(self, execution_id=None, span_id=None):
        self.execution_id = execution_id
        self.span_id = span_id


def _get_current_context():
    return (
        flask.g.execution_id_context
        if flask.has_request_context() and "execution_id_context" in flask.g
        else None
    )


def _set_current_context(context):
    if flask.has_request_context():
        flask.g.execution_id_context = context


def _generate_execution_id():
    return "".join(
        _EXECUTION_ID_CHARSET[random.randrange(len(_EXECUTION_ID_CHARSET))]
        for _ in range(_EXECUTION_ID_LENGTH)
    )


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


# Sets execution id and span id for the request
def set_execution_context(request, enable_id_logging=False):
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
            trace_context = re.match(
                _TRACE_CONTEXT_REGEX_PATTERN,
                request.headers.get(TRACE_CONTEXT_REQUEST_HEADER, ""),
            )
            execution_id = request.headers.get(EXECUTION_ID_REQUEST_HEADER)
            span_id = trace_context.group("span_id") if trace_context else None
            _set_current_context(ExecutionContext(execution_id, span_id))

            with stderr_redirect, stdout_redirect:
                return view_function(*args, **kwargs)

        return wrapper

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
