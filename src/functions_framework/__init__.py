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
import os.path
import pathlib
import sys
import types

import flask
import werkzeug

from functions_framework.exceptions import (
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


class _Event(object):
    """Event passed to background functions."""

    # Supports both v1beta1 and v1beta2 event formats.
    def __init__(
        self,
        context=None,
        data="",
        eventId="",
        timestamp="",
        eventType="",
        resource="",
        **kwargs
    ):
        self.context = context
        if not self.context:
            self.context = {
                "eventId": eventId,
                "timestamp": timestamp,
                "eventType": eventType,
                "resource": resource,
            }
        self.data = data


def _http_view_func_wrapper(function, request):
    def view_func(path):
        return function(request._get_current_object())

    return view_func


def _is_binary_cloud_event(request):
    return (
        request.headers.get("ce-type")
        and request.headers.get("ce-specversion")
        and request.headers.get("ce-source")
        and request.headers.get("ce-id")
    )


def _event_view_func_wrapper(function, request):
    def view_func(path):
        if _is_binary_cloud_event(request):
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
            event_data = request.get_json()
            if not event_data:
                flask.abort(400)
            event_object = _Event(**event_data)
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

    # 5. Execute the module
    spec.loader.exec_module(source_module)

    app = flask.Flask(target, template_folder=template_folder)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    # 6. Handle legacy GCF Python 3.7 behavior
    if os.environ.get("ENTRY_POINT"):
        os.environ["FUNCTION_TRIGGER_TYPE"] = signature_type
        os.environ["FUNCTION_NAME"] = os.environ.get("K_SERVICE", target)
        app.make_response_original = app.make_response

        def handle_none(rv):
            if rv is None:
                rv = "OK"
            return app.make_response_original(rv)

        app.make_response = handle_none

    # Extract the target function from the source file
    try:
        function = getattr(source_module, target)
    except AttributeError:
        raise MissingTargetException(
            "File {source} is expected to contain a function named {target}".format(
                source=source, target=target
            )
        )

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
