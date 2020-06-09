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


from cloudevents.sdk.event import v1
from cloudevents.sdk import marshaller

DEFAULT_SOURCE = os.path.realpath("./main.py")
DEFAULT_SIGNATURE_TYPE = "http"


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


def _get_cloud_event_version(request):
    headers = request.headers
    # TODO: not 100% robust
    if headers.get("Content-Type") == "application/cloudevents+json":
        return v1.Event()

    return None

def _convert_request_to_event(request, cloud_event_def):
    # TODO: not 100% robust
    m = marshaller.NewDefaultHTTPMarshaller()
    data = io.StringIO(request.get_data(as_text=True))
    return m.FromRequest(cloud_event_def, request.headers, data, json.loads)


def _http_view_func_wrapper(function, request):
    def view_func(path):
        # How do we preserve backwards compatibility?
        cloud_event_def = _get_cloud_event_version(request._get_current_object())
        if cloud_event_def is None:
            return function(request._get_current_object())
        else:
            return function(_convert_request_to_event(request, cloud_event_def))

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
            cloud_event_def = _get_cloud_event_version(request)
            if cloud_event_def is None:
                # This is a regular CloudEvent
                event_data = request.get_json()
                if not event_data:
                    flask.abort(400)
                event_object = _Event(**event_data)
                data = event_object.data
                context = Context(**event_object.context)
                function(data, context)
            else:
                # We have a bonafide event from the SDK. Let's use it.
                # TODO(joelgerard): Starting to become a long fn.
                event = _convert_request_to_event(request, cloud_event_def)
                # TODO: Fix context
                # context = Context(**event.context)
                function(event) #, context)

        return "OK"

    return view_func


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

    # Load the source file
    spec = importlib.util.spec_from_file_location("__main__", source)
    source_module = importlib.util.module_from_spec(spec)
    sys.path.append(os.path.dirname(os.path.realpath(source)))
    spec.loader.exec_module(source_module)

    app = flask.Flask(target, template_folder=template_folder)

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
