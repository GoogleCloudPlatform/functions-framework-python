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
import importlib.util
import io
import json
import logging
import os.path
import pathlib
import sys
import types

import cloudevents.exceptions as cloud_exceptions
import flask
import werkzeug

from cloudevents.http import from_http, is_binary

from functions_framework import event_conversion
from functions_framework.background_event import BackgroundEvent
from functions_framework.exceptions import (
    EventConversionException,
    FunctionsFrameworkException,
    InvalidConfigurationException,
    InvalidTargetTypeException,
    MissingSourceException,
    MissingTargetException,
)
from google.cloud.functions.context import Context

DEFAULT_SOURCE = os.path.realpath("./main.py")
DEFAULT_SIGNATURE_TYPE = "http"
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

_FUNCTION_STATUS_HEADER_FIELD = "X-Google-Status"
_CRASH = "crash"

_CLOUDEVENT_MIME_TYPE = "application/cloudevents+json"


class _LoggingHandler(io.TextIOWrapper):
    """Logging replacement for stdout and stderr in GCF Python 3.7."""

    def __init__(self, level, stderr=sys.stderr):
        io.TextIOWrapper.__init__(self, io.StringIO(), encoding=stderr.encoding)
        self.level = level
        self.stderr = stderr

    def write(self, out):
        payload = dict(severity=self.level, message=out.rstrip("\n"))
        return self.stderr.write(json.dumps(payload) + "\n")


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
    def view_func(path):
        return function(request._get_current_object())

    return view_func


def _run_cloudevent(function, request):
    data = request.get_data()
    event = from_http(request.headers, data)
    function(event)


def _cloudevent_view_func_wrapper(function, request):
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
            function(event_conversion.background_event_to_cloudevent(request))
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
        if event_conversion.is_convertable_cloudevent(request):
            # Convert this CloudEvent to the equivalent background event data and context.
            data, context = event_conversion.cloudevent_to_background_event(request)
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


def read_request(response):
    """
    Force the framework to read the entire request before responding, to avoid
    connection errors when returning prematurely.
    """

    flask.request.get_data()
    return response


def crash_handler(e):
    """
    Return crash header to allow logging 'crash' message in logs.
    """
    return str(e), 500, {_FUNCTION_STATUS_HEADER_FIELD: _CRASH}


def create_app(target=None, source=None, signature_type=None):
    # Get the configured function target
    target = target or os.environ.get("FUNCTION_TARGET", "")
    # Set the environment variable if it wasn't already
    os.environ["FUNCTION_TARGET"] = target

    if not target:
        raise InvalidConfigurationException(
            "Target is not specified (FUNCTION_TARGET environment variable not set)"
        )

    # Get the configured function source
    source = source or os.environ.get("FUNCTION_SOURCE", DEFAULT_SOURCE)

    # Python 3.5: os.path.exist does not support PosixPath
    source = str(source)

    # Set the template folder relative to the source path
    # Python 3.5: join does not support PosixPath
    template_folder = str(pathlib.Path(source).parent / "templates")

    if not os.path.exists(source):
        raise MissingSourceException(
            "File {source} that is expected to define function doesn't exist".format(
                source=source
            )
        )

    # Get the configured function signature type
    signature_type = signature_type or os.environ.get(
        "FUNCTION_SIGNATURE_TYPE", DEFAULT_SIGNATURE_TYPE
    )
    # Set the environment variable if it wasn't already
    os.environ["FUNCTION_SIGNATURE_TYPE"] = signature_type

    # Load the source file:
    # 1. Extract the module name from the source path
    realpath = os.path.realpath(source)
    directory, filename = os.path.split(realpath)
    name, extension = os.path.splitext(filename)

    # 2. Create a new module
    spec = importlib.util.spec_from_file_location(name, realpath)
    source_module = importlib.util.module_from_spec(spec)

    # 3. Add the directory of the source to sys.path to allow the function to
    # load modules relative to its location
    sys.path.append(directory)

    # 4. Add the module to sys.modules
    sys.modules[name] = source_module

    # 5. Create the application
    app = flask.Flask(target, template_folder=template_folder)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.register_error_handler(500, crash_handler)
    global errorhandler
    errorhandler = app.errorhandler

    # 6. Execute the module, within the application context
    with app.app_context():
        spec.loader.exec_module(source_module)

    # Handle legacy GCF Python 3.7 behavior
    if os.environ.get("ENTRY_POINT"):
        os.environ["FUNCTION_TRIGGER_TYPE"] = signature_type
        os.environ["FUNCTION_NAME"] = os.environ.get("K_SERVICE", target)
        app.make_response_original = app.make_response

        def handle_none(rv):
            if rv is None:
                rv = "OK"
            return app.make_response_original(rv)

        app.make_response = handle_none

        # Handle log severity backwards compatibility
        sys.stdout = _LoggingHandler("INFO", sys.stderr)
        sys.stderr = _LoggingHandler("ERROR", sys.stderr)
        setup_logging()

    # Extract the target function from the source file
    if not hasattr(source_module, target):
        raise MissingTargetException(
            "File {source} is expected to contain a function named {target}".format(
                source=source, target=target
            )
        )
    function = getattr(source_module, target)

    # Check that it is a function
    if not isinstance(function, types.FunctionType):
        raise InvalidTargetTypeException(
            "The function defined in file {source} as {target} needs to be of "
            "type function. Got: invalid type {target_type}".format(
                source=source, target=target, target_type=type(function)
            )
        )

    # Mount the function at the root. Support GCF's default path behavior
    # Modify the url_map and view_functions directly here instead of using
    # add_url_rule in order to create endpoints that route all methods
    if signature_type == "http":
        app.url_map.add(
            werkzeug.routing.Rule("/", defaults={"path": ""}, endpoint="run")
        )
        app.url_map.add(werkzeug.routing.Rule("/robots.txt", endpoint="error"))
        app.url_map.add(werkzeug.routing.Rule("/favicon.ico", endpoint="error"))
        app.url_map.add(werkzeug.routing.Rule("/<path:path>", endpoint="run"))
        app.view_functions["run"] = _http_view_func_wrapper(function, flask.request)
        app.view_functions["error"] = lambda: flask.abort(404, description="Not Found")
        app.after_request(read_request)
    elif signature_type == "event":
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
    elif signature_type == "cloudevent":
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

        app.view_functions[signature_type] = _cloudevent_view_func_wrapper(
            function, flask.request
        )
    else:
        raise FunctionsFrameworkException(
            "Invalid signature type: {signature_type}".format(
                signature_type=signature_type
            )
        )

    return app


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
