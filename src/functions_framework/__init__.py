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

import enum
import importlib.util
import io
import json
import os.path
import pathlib
import sys
import types

import cloudevents.sdk
import cloudevents.sdk.event
import cloudevents.sdk.event.v1
import cloudevents.sdk.marshaller
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


class _EventType(enum.Enum):
    LEGACY = 1
    CLOUDEVENT_BINARY = 2
    CLOUDEVENT_STRUCTURED = 3


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


def _get_cloudevent_version():
    return cloudevents.sdk.event.v1.Event()


def _run_legacy_event(function, request):
    event_data = request.get_json()
    if not event_data:
        flask.abort(400)
    event_object = _Event(**event_data)
    data = event_object.data
    context = Context(**event_object.context)
    function(data, context)


def _run_binary_cloudevent(function, request, cloudevent_def):
    data = io.BytesIO(request.get_data())
    http_marshaller = cloudevents.sdk.marshaller.NewDefaultHTTPMarshaller()
    event = http_marshaller.FromRequest(
        cloudevent_def, request.headers, data, json.load
    )

    function(event)


def _run_structured_cloudevent(function, request, cloudevent_def):
    data = io.StringIO(request.get_data(as_text=True))
    m = cloudevents.sdk.marshaller.NewDefaultHTTPMarshaller()
    event = m.FromRequest(cloudevent_def, request.headers, data, json.loads)
    function(event)


def _get_event_type(request):
    if (
        request.headers.get("ce-type")
        and request.headers.get("ce-specversion")
        and request.headers.get("ce-source")
        and request.headers.get("ce-id")
    ):
        return _EventType.CLOUDEVENT_BINARY
    elif request.headers.get("Content-Type") == "application/cloudevents+json":
        return _EventType.CLOUDEVENT_STRUCTURED
    else:
        return _EventType.LEGACY


def _event_view_func_wrapper(function, request):
    def view_func(path):
        if _get_event_type(request) == _EventType.LEGACY:
            _run_legacy_event(function, request)
        else:
            # here for defensive backwards compatibility in case we make a mistake in rollout.
            flask.abort(
                400,
                description="The FUNCTION_SIGNATURE_TYPE for this function is set to event "
                "but no Google Cloud Functions Event was given. If you are using CloudEvents set "
                "FUNCTION_SIGNATURE_TYPE=cloudevent",
            )

        return "OK"

    return view_func


def _cloudevent_view_func_wrapper(function, request):
    def view_func(path):
        cloudevent_def = _get_cloudevent_version()
        event_type = _get_event_type(request)
        if event_type == _EventType.CLOUDEVENT_STRUCTURED:
            _run_structured_cloudevent(function, request, cloudevent_def)
        elif event_type == _EventType.CLOUDEVENT_BINARY:
            _run_binary_cloudevent(function, request, cloudevent_def)
        else:
            flask.abort(
                400,
                description="Function was defined with FUNCTION_SIGNATURE_TYPE=cloudevent "
                " but it did not receive a cloudevent as a request.",
            )

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
    elif signature_type == "event" or signature_type == "cloudevent":
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

        # Add a dummy endpoint for GET /
        app.url_map.add(werkzeug.routing.Rule("/", endpoint="get", methods=["GET"]))
        app.view_functions["get"] = lambda: ""

        # Add the view functions
        app.view_functions["event"] = _event_view_func_wrapper(function, flask.request)
        app.view_functions["cloudevent"] = _cloudevent_view_func_wrapper(
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
