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

import functools
import inspect
import io
import json
import logging
import os.path
import pathlib
import sys
import types

from inspect import signature
from typing import Callable, Type

import cloudevents.exceptions as cloud_exceptions
import flask
import werkzeug

from cloudevents.http import from_http, is_binary
from cloudevents.http.event import CloudEvent

from functions_framework import _function_registry, _typed_event, event_conversion
from functions_framework.background_event import BackgroundEvent
from functions_framework.exceptions import (
    EventConversionException,
    FunctionsFrameworkException,
    MissingSourceException,
)
from google.cloud.functions.context import Context

_FUNCTION_STATUS_HEADER_FIELD = "X-Google-Status"
_CRASH = "crash"

_CLOUDEVENT_MIME_TYPE = "application/cloudevents+json"

CloudEventFunction = Callable[[CloudEvent], None]
HTTPFunction = Callable[[flask.Request], flask.typing.ResponseReturnValue]


class _LoggingHandler(io.TextIOWrapper):
    """Logging replacement for stdout and stderr in GCF Python 3.7."""

    def __init__(self, level, stderr=sys.stderr):
        io.TextIOWrapper.__init__(self, io.StringIO(), encoding=stderr.encoding)
        self.level = level
        self.stderr = stderr

    def write(self, out):
        payload = dict(severity=self.level, message=out.rstrip("\n"))
        return self.stderr.write(json.dumps(payload) + "\n")


def cloud_event(func: CloudEventFunction) -> CloudEventFunction:
    """Decorator that registers cloudevent as user function signature type."""
    _function_registry.REGISTRY_MAP[
        func.__name__
    ] = _function_registry.CLOUDEVENT_SIGNATURE_TYPE

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def typed(*args):
    def _typed(func):
        _typed_event.register_typed_event(input_type, func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    # no input type provided as a parameter, we need to use reflection
    # e.g function declaration:
    # @typed
    # def myfunc(x:input_type)
    if len(args) == 1 and isinstance(args[0], types.FunctionType):
        input_type = None
        return _typed(args[0])

    # input type provided as a parameter to the decorator
    # e.g. function declaration
    # @typed(input_type)
    # def myfunc(x)
    else:
        input_type = args[0]
        return _typed


def http(func: HTTPFunction) -> HTTPFunction:
    """Decorator that registers http as user function signature type."""
    _function_registry.REGISTRY_MAP[
        func.__name__
    ] = _function_registry.HTTP_SIGNATURE_TYPE

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def setup_logging():
    logging.getLogger().setLevel(logging.INFO)
    info_handler = logging.StreamHandler(sys.stdout)
    info_handler.setLevel(logging.NOTSET)
    info_handler.addFilter(lambda record: record.levelno <= logging.INFO)
    logging.getLogger().addHandler(info_handler)

    warn_handler = logging.StreamHandler(sys.stderr)
    warn_handler.setLevel(logging.WARNING)
    logging.getLogger().addHandler(warn_handler)


def _http_view_func_wrapper(function, request):
    @functools.wraps(function)
    def view_func(path):
        return function(request._get_current_object())

    return view_func


def _run_cloud_event(function, request):
    data = request.get_data()
    event = from_http(request.headers, data)
    function(event)


def _typed_event_func_wrapper(function, request, inputType: Type):
    def view_func(path):
        try:
            data = request.get_json()
            input = inputType.from_dict(data)
            response = function(input)
            if response is None:
                return "", 200
            if response.__class__.__module__ == "builtins":
                return response
            _typed_event._validate_return_type(response)
            return json.dumps(response.to_dict())
        except Exception as e:
            raise FunctionsFrameworkException(
                "Function execution failed with the error"
            ) from e

    return view_func


def _cloud_event_view_func_wrapper(function, request):
    def view_func(path):
        ce_exception = None
        event = None
        try:
            event = from_http(request.headers, request.get_data())
        except (
            cloud_exceptions.MissingRequiredFields,
            cloud_exceptions.InvalidRequiredFields,
        ) as e:
            ce_exception = e

        if not ce_exception:
            function(event)
            return "OK"

        # Not a CloudEvent. Try converting to a CloudEvent.
        try:
            function(event_conversion.background_event_to_cloud_event(request))
        except EventConversionException as e:
            flask.abort(
                400,
                description=(
                    "Function was defined with FUNCTION_SIGNATURE_TYPE=cloudevent but"
                    " parsing CloudEvent failed and converting from background event to"
                    f" CloudEvent also failed.\nGot HTTP headers: {request.headers}\nGot"
                    f" data: {request.get_data()}\nGot CloudEvent exception: {repr(ce_exception)}"
                    f"\nGot background event conversion exception: {repr(e)}"
                ),
            )
        return "OK"

    return view_func


def _event_view_func_wrapper(function, request):
    def view_func(path):
        if event_conversion.is_convertable_cloud_event(request):
            # Convert this CloudEvent to the equivalent background event data and context.
            data, context = event_conversion.cloud_event_to_background_event(request)
            function(data, context)
        elif is_binary(request.headers):
            # Support CloudEvents in binary content mode, with data being the
            # whole request body and context attributes retrieved from request
            # headers.
            data = request.get_data()
            context = Context(
                eventId=request.headers.get("ce-eventId"),
                timestamp=request.headers.get("ce-timestamp"),
                eventType=request.headers.get("ce-eventType"),
                resource=request.headers.get("ce-resource"),
            )
            function(data, context)
        else:
            # This is a regular CloudEvent
            event_data = event_conversion.marshal_background_event_data(request)
            if not event_data:
                flask.abort(400)
            event_object = BackgroundEvent(**event_data)
            data = event_object.data
            context = Context(**event_object.context)
            function(data, context)

        return "OK"

    return view_func


def _configure_app(app, function, signature_type):
    # Mount the function at the root. Support GCF's default path behavior
    # Modify the url_map and view_functions directly here instead of using
    # add_url_rule in order to create endpoints that route all methods
    if signature_type == _function_registry.HTTP_SIGNATURE_TYPE:
        app.url_map.add(
            werkzeug.routing.Rule("/", defaults={"path": ""}, endpoint="run")
        )
        app.url_map.add(werkzeug.routing.Rule("/robots.txt", endpoint="error"))
        app.url_map.add(werkzeug.routing.Rule("/favicon.ico", endpoint="error"))
        app.url_map.add(werkzeug.routing.Rule("/<path:path>", endpoint="run"))
        app.view_functions["run"] = _http_view_func_wrapper(function, flask.request)
        app.view_functions["error"] = lambda: flask.abort(404, description="Not Found")
        app.after_request(read_request)
    elif signature_type == _function_registry.BACKGROUNDEVENT_SIGNATURE_TYPE:
        app.url_map.add(
            werkzeug.routing.Rule(
                "/", defaults={"path": ""}, endpoint="run", methods=["POST"]
            )
        )
        app.url_map.add(
            werkzeug.routing.Rule("/<path:path>", endpoint="run", methods=["POST"])
        )
        app.view_functions["run"] = _event_view_func_wrapper(function, flask.request)
        # Add a dummy endpoint for GET /
        app.url_map.add(werkzeug.routing.Rule("/", endpoint="get", methods=["GET"]))
        app.view_functions["get"] = lambda: ""
    elif signature_type == _function_registry.CLOUDEVENT_SIGNATURE_TYPE:
        app.url_map.add(
            werkzeug.routing.Rule(
                "/", defaults={"path": ""}, endpoint=signature_type, methods=["POST"]
            )
        )
        app.url_map.add(
            werkzeug.routing.Rule(
                "/<path:path>", endpoint=signature_type, methods=["POST"]
            )
        )

        app.view_functions[signature_type] = _cloud_event_view_func_wrapper(
            function, flask.request
        )
    elif signature_type == _function_registry.TYPED_SIGNATURE_TYPE:
        app.url_map.add(
            werkzeug.routing.Rule(
                "/", defaults={"path": ""}, endpoint=signature_type, methods=["POST"]
            )
        )
        app.url_map.add(
            werkzeug.routing.Rule(
                "/<path:path>", endpoint=signature_type, methods=["POST"]
            )
        )
        input_type = _function_registry.get_func_input_type(function.__name__)
        app.view_functions[signature_type] = _typed_event_func_wrapper(
            function, flask.request, input_type
        )
    else:
        raise FunctionsFrameworkException(
            "Invalid signature type: {signature_type}".format(
                signature_type=signature_type
            )
        )


def read_request(response):
    """
    Force the framework to read the entire request before responding, to avoid
    connection errors when returning prematurely. Skipped on streaming responses
    as these may continue to operate on the request after they are returned.
    """

    if not response.is_streamed:
        flask.request.get_data()

    return response


def crash_handler(e):
    """
    Return crash header to allow logging 'crash' message in logs.
    """
    return str(e), 500, {_FUNCTION_STATUS_HEADER_FIELD: _CRASH}


def create_app(target=None, source=None, signature_type=None):
    target = _function_registry.get_function_target(target)
    source = _function_registry.get_function_source(source)

    # Set the template folder relative to the source path
    # Python 3.5: join does not support PosixPath
    template_folder = str(pathlib.Path(source).parent / "templates")

    if not os.path.exists(source):
        raise MissingSourceException(
            "File {source} that is expected to define function doesn't exist".format(
                source=source
            )
        )

    source_module, spec = _function_registry.load_function_module(source)

    # Create the application
    _app = flask.Flask(target, template_folder=template_folder)
    _app.register_error_handler(500, crash_handler)
    global errorhandler
    errorhandler = _app.errorhandler

    # Handle legacy GCF Python 3.7 behavior
    if os.environ.get("ENTRY_POINT"):
        os.environ["FUNCTION_NAME"] = os.environ.get("K_SERVICE", target)
        _app.make_response_original = _app.make_response

        def handle_none(rv):
            if rv is None:
                rv = "OK"
            return _app.make_response_original(rv)

        _app.make_response = handle_none

        # Handle log severity backwards compatibility
        sys.stdout = _LoggingHandler("INFO", sys.stderr)
        sys.stderr = _LoggingHandler("ERROR", sys.stderr)
        setup_logging()

    # Execute the module, within the application context
    with _app.app_context():
        try:
            spec.loader.exec_module(source_module)
            function = _function_registry.get_user_function(
                source, source_module, target
            )
        except Exception as e:
            if werkzeug.serving.is_running_from_reloader():
                # When reloading, print out the error immediately, but raise
                # it later so the debugger or server can handle it.
                import traceback

                traceback.print_exc()
                err = e

                def function(*_args, **_kwargs):
                    raise err from None

            else:
                # When not reloading, raise the error immediately so the
                # command fails.
                raise e from None

    # Get the configured function signature type
    signature_type = _function_registry.get_func_signature_type(target, signature_type)

    _configure_app(_app, function, signature_type)

    return _app


class LazyWSGIApp:
    """
    Wrap the WSGI app in a lazily initialized wrapper to prevent initialization
    at import-time
    """

    def __init__(self, target=None, source=None, signature_type=None):
        # Support HTTP frameworks which support WSGI callables.
        # Note: this ability is currently broken in Gunicorn 20.0, and
        # environment variables should be used for configuration instead:
        # https://github.com/benoitc/gunicorn/issues/2159
        self.target = target
        self.source = source
        self.signature_type = signature_type

        # Placeholder for the app which will be initialized on first call
        self.app = None

    def __call__(self, *args, **kwargs):
        if not self.app:
            self.app = create_app(self.target, self.source, self.signature_type)
        return self.app(*args, **kwargs)


app = LazyWSGIApp()


class DummyErrorHandler:
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        return self


errorhandler = DummyErrorHandler()
