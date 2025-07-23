# Copyright 2025 Google LLC
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

import asyncio
import contextvars
import functools
import inspect
import logging
import logging.config
import os
import traceback

from typing import Any, Awaitable, Callable, Dict, Tuple, Union

from cloudevents.http import from_http
from cloudevents.http.event import CloudEvent
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from functions_framework import (
    _enable_execution_id_logging,
    _function_registry,
    execution_id,
)
from functions_framework.exceptions import (
    FunctionsFrameworkException,
    MissingSourceException,
)

HTTPResponse = Union[
    Response,  # Functions can return a full Starlette Response object
    str,  # Str returns are wrapped in Response(result)
    Dict[Any, Any],  # Dict returns are wrapped in JSONResponse(result)
    Tuple[Any, int],  # Flask-style (content, status_code) supported
    None,  # None raises HTTPException
]

_FUNCTION_STATUS_HEADER_FIELD = "X-Google-Status"
_CRASH = "crash"

CloudEventFunction = Callable[[CloudEvent], Union[None, Awaitable[None]]]
HTTPFunction = Callable[[Request], Union[HTTPResponse, Awaitable[HTTPResponse]]]


def cloud_event(func: CloudEventFunction) -> CloudEventFunction:
    """Decorator that registers cloudevent as user function signature type."""
    _function_registry.REGISTRY_MAP[func.__name__] = (
        _function_registry.CLOUDEVENT_SIGNATURE_TYPE
    )
    _function_registry.ASGI_FUNCTIONS.add(func.__name__)
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def http(func: HTTPFunction) -> HTTPFunction:
    """Decorator that registers http as user function signature type."""
    _function_registry.REGISTRY_MAP[func.__name__] = (
        _function_registry.HTTP_SIGNATURE_TYPE
    )
    _function_registry.ASGI_FUNCTIONS.add(func.__name__)

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def _http_func_wrapper(function, is_async, enable_id_logging=False):
    @execution_id.set_execution_context_async(enable_id_logging)
    @functools.wraps(function)
    async def handler(request):
        if is_async:
            result = await function(request)
        else:
            # TODO: Use asyncio.to_thread when we drop Python 3.8 support
            loop = asyncio.get_event_loop()
            ctx = contextvars.copy_context()
            result = await loop.run_in_executor(None, ctx.run, function, request)
        if isinstance(result, str):
            return Response(result)
        elif isinstance(result, dict):
            return JSONResponse(result)
        elif isinstance(result, tuple) and len(result) == 2:
            content, status_code = result
            if isinstance(content, dict):
                return JSONResponse(content, status_code=status_code)
            else:
                return Response(content, status_code=status_code)
        elif result is None:
            raise HTTPException(status_code=500, detail="No response returned")
        else:
            return result

    return handler


def _cloudevent_func_wrapper(function, is_async, enable_id_logging=False):
    @execution_id.set_execution_context_async(enable_id_logging)
    @functools.wraps(function)
    async def handler(request):
        data = await request.body()

        try:
            event = from_http(request.headers, data)
        except Exception as e:
            raise HTTPException(
                400, detail=f"Bad Request: Got CloudEvent exception: {repr(e)}"
            )
        if is_async:
            await function(event)
        else:
            # TODO: Use asyncio.to_thread when we drop Python 3.8 support
            loop = asyncio.get_event_loop()
            ctx = contextvars.copy_context()
            await loop.run_in_executor(None, ctx.run, function, event)
        return Response("OK")

    return handler


async def _handle_not_found(request: Request):
    raise HTTPException(status_code=404, detail="Not Found")


def _configure_app_execution_id_logging():
    logging.config.dictConfig(
        {
            "version": 1,
            "handlers": {
                "asgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://functions_framework.execution_id.logging_stream",
                },
            },
            "root": {"level": "WARNING", "handlers": ["asgi"]},
        }
    )


class ExceptionHandlerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":  # pragma: no cover
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            logger = logging.getLogger()
            tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
            tb_text = "".join(tb_lines)

            path = scope.get("path", "/")
            method = scope.get("method", "GET")
            error_msg = f"Exception on {path} [{method}]\n{tb_text}".rstrip()

            logger.error(error_msg)

            headers = [
                [b"content-type", b"text/plain"],
                [_FUNCTION_STATUS_HEADER_FIELD.encode(), _CRASH.encode()],
            ]

            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": headers,
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"Internal Server Error",
                }
            )
            # Don't re-raise to prevent starlette from printing traceback again


def create_asgi_app_from_module(target, source, signature_type, source_module, spec):
    """Create an ASGI application from an already-loaded module.

    Args:
        target: The name of the target function to invoke
        source: The source file containing the function
        signature_type: The signature type of the function
        source_module: The already-loaded module
        spec: The module spec

    Returns:
        A Starlette ASGI application instance
    """
    enable_id_logging = _enable_execution_id_logging()
    if enable_id_logging:  # pragma: no cover
        _configure_app_execution_id_logging()

    function = _function_registry.get_user_function(source, source_module, target)
    signature_type = _function_registry.get_func_signature_type(target, signature_type)

    return _create_asgi_app_with_function(function, signature_type, enable_id_logging)


def create_asgi_app(target=None, source=None, signature_type=None):
    """Create an ASGI application for the function.

    Args:
        target: The name of the target function to invoke
        source: The source file containing the function
        signature_type: The signature type of the function
                       ('http', 'event', 'cloudevent', or 'typed')

    Returns:
        A Starlette ASGI application instance
    """
    target = _function_registry.get_function_target(target)
    source = _function_registry.get_function_source(source)

    if not os.path.exists(source):
        raise MissingSourceException(
            f"File {source} that is expected to define function doesn't exist"
        )

    source_module, spec = _function_registry.load_function_module(source)

    enable_id_logging = _enable_execution_id_logging()
    if enable_id_logging:
        _configure_app_execution_id_logging()

    spec.loader.exec_module(source_module)
    function = _function_registry.get_user_function(source, source_module, target)
    signature_type = _function_registry.get_func_signature_type(target, signature_type)

    return _create_asgi_app_with_function(function, signature_type, enable_id_logging)


def _create_asgi_app_with_function(function, signature_type, enable_id_logging):
    """Create an ASGI app with the given function and signature type."""
    is_async = inspect.iscoroutinefunction(function)
    routes = []
    if signature_type == _function_registry.HTTP_SIGNATURE_TYPE:
        http_handler = _http_func_wrapper(function, is_async, enable_id_logging)
        routes.append(
            Route(
                "/",
                endpoint=http_handler,
                methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
            ),
        )
        routes.append(Route("/robots.txt", endpoint=_handle_not_found, methods=["GET"]))
        routes.append(
            Route("/favicon.ico", endpoint=_handle_not_found, methods=["GET"])
        )
        routes.append(
            Route(
                "/{path:path}",
                endpoint=http_handler,
                methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
            )
        )
    elif signature_type == _function_registry.CLOUDEVENT_SIGNATURE_TYPE:
        cloudevent_handler = _cloudevent_func_wrapper(
            function, is_async, enable_id_logging
        )
        routes.append(
            Route("/{path:path}", endpoint=cloudevent_handler, methods=["POST"])
        )
        routes.append(Route("/", endpoint=cloudevent_handler, methods=["POST"]))
    elif signature_type == _function_registry.TYPED_SIGNATURE_TYPE:
        raise FunctionsFrameworkException(
            f"ASGI server does not support typed events (signature type: '{signature_type}'). "
        )
    elif signature_type == _function_registry.BACKGROUNDEVENT_SIGNATURE_TYPE:
        raise FunctionsFrameworkException(
            f"ASGI server does not support legacy background events (signature type: '{signature_type}'). "
            "Use 'cloudevent' signature type instead."
        )
    else:
        raise FunctionsFrameworkException(
            f"Unsupported signature type for ASGI server: {signature_type}"
        )

    app = Starlette(
        routes=routes,
        middleware=[
            Middleware(ExceptionHandlerMiddleware),
            Middleware(execution_id.AsgiMiddleware),
        ],
    )

    return app


class LazyASGIApp:
    """
    Wrap the ASGI app in a lazily initialized wrapper to prevent initialization
    at import-time
    """

    def __init__(self, target=None, source=None, signature_type=None):
        self.target = target
        self.source = source
        self.signature_type = signature_type

        self.app = None
        self._app_initialized = False

    async def __call__(self, scope, receive, send):
        if not self._app_initialized:
            self.app = create_asgi_app(self.target, self.source, self.signature_type)
            self._app_initialized = True
        await self.app(scope, receive, send)


app = LazyASGIApp()
