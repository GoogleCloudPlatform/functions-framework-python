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

import pathlib
import re
import sys
import tempfile

from unittest.mock import AsyncMock, Mock, call

import pytest

from starlette.testclient import TestClient

from functions_framework import exceptions
from functions_framework.aio import (
    LazyASGIApp,
    _cloudevent_func_wrapper,
    _http_func_wrapper,
    _is_asgi_app,
    create_asgi_app,
)

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"


def test_import_error_without_starlette(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name.startswith("starlette"):
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    # Remove the module from sys.modules to force re-import
    if "functions_framework.aio" in sys.modules:
        del sys.modules["functions_framework.aio"]

    with pytest.raises(exceptions.FunctionsFrameworkException) as excinfo:
        import functions_framework.aio

    assert "Starlette is not installed" in str(excinfo.value)
    assert "pip install functions-framework[async]" in str(excinfo.value)


def test_invalid_function_definition_missing_function_file():
    source = TEST_FUNCTIONS_DIR / "missing_function_file" / "main.py"
    target = "function"

    with pytest.raises(exceptions.MissingSourceException) as excinfo:
        create_asgi_app(target, source)

    assert re.match(
        r"File .* that is expected to define function doesn't exist", str(excinfo.value)
    )


def test_asgi_typed_signature_not_supported():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "typed_event.py"
    target = "function_typed"

    with pytest.raises(exceptions.FunctionsFrameworkException) as excinfo:
        create_asgi_app(target, source, "typed")

    assert "ASGI server does not support typed events (signature type: 'typed')" in str(
        excinfo.value
    )


def test_asgi_background_event_not_supported():
    source = TEST_FUNCTIONS_DIR / "background_trigger" / "main.py"
    target = "function"

    with pytest.raises(exceptions.FunctionsFrameworkException) as excinfo:
        create_asgi_app(target, source, "event")

    assert (
        "ASGI server does not support legacy background events (signature type: 'event')"
        in str(excinfo.value)
    )
    assert "Use 'cloudevent' signature type instead" in str(excinfo.value)


@pytest.mark.asyncio
async def test_lazy_asgi_app(monkeypatch):
    actual_app = AsyncMock()
    create_asgi_app_mock = Mock(return_value=actual_app)
    monkeypatch.setattr("functions_framework.aio.create_asgi_app", create_asgi_app_mock)

    # Test that it's lazy
    target, source, signature_type = "func", "source.py", "http"
    lazy_app = LazyASGIApp(target, source, signature_type)

    assert lazy_app.app is None
    assert lazy_app._app_initialized is False

    # Mock ASGI call parameters
    scope = {"type": "http", "method": "GET", "path": "/"}
    receive = AsyncMock()
    send = AsyncMock()

    # Test that it's initialized when called
    await lazy_app(scope, receive, send)

    assert lazy_app.app is actual_app
    assert lazy_app._app_initialized is True
    assert create_asgi_app_mock.call_count == 1
    assert create_asgi_app_mock.call_args == call(target, source, signature_type)

    # Verify the app was called
    actual_app.assert_called_once_with(scope, receive, send)

    # Test that subsequent calls use the same app
    create_asgi_app_mock.reset_mock()
    actual_app.reset_mock()

    await lazy_app(scope, receive, send)

    assert create_asgi_app_mock.call_count == 0  # Should not create app again
    actual_app.assert_called_once_with(scope, receive, send)  # Should be called again


@pytest.mark.asyncio
async def test_http_func_wrapper_json_response():
    async def http_func(request):
        return {"message": "hello", "count": 42}

    wrapper = _http_func_wrapper(http_func, is_async=True)

    request = Mock()
    request.headers = Mock()
    request.headers.get = Mock(return_value="")
    response = await wrapper(request)

    assert response.__class__.__name__ == "JSONResponse"
    assert b'"message":"hello"' in response.body
    assert b'"count":42' in response.body


@pytest.mark.asyncio
async def test_http_func_wrapper_sync_function():
    def sync_http_func(request):
        return "sync response"

    wrapper = _http_func_wrapper(sync_http_func, is_async=False)

    request = Mock()
    request.headers = Mock()
    request.headers.get = Mock(return_value="")
    response = await wrapper(request)

    assert response.__class__.__name__ == "Response"
    assert response.body == b"sync response"


@pytest.mark.asyncio
async def test_cloudevent_func_wrapper_sync_function():
    called_with_event = None

    def sync_cloud_event(event):
        nonlocal called_with_event
        called_with_event = event

    wrapper = _cloudevent_func_wrapper(sync_cloud_event, is_async=False)

    request = Mock()
    request.body = AsyncMock(
        return_value=b'{"specversion": "1.0", "type": "test.event", "source": "test-source", "id": "123", "data": {"test": "data"}}'
    )
    request.headers = {"content-type": "application/cloudevents+json"}

    response = await wrapper(request)

    assert response.body == b"OK"
    assert response.status_code == 200

    assert called_with_event is not None
    assert called_with_event["type"] == "test.event"
    assert called_with_event["source"] == "test-source"


def test_detects_starlette_app():
    from starlette.applications import Starlette

    app = Starlette()
    assert _is_asgi_app(app) is True


def test_detects_fastapi_app():
    from fastapi import FastAPI

    app = FastAPI()
    assert _is_asgi_app(app) is True


def test_detects_bare_asgi_callable():
    async def asgi_app(scope, receive, send):
        pass

    assert _is_asgi_app(asgi_app) is True


def test_rejects_non_asgi_functions():
    def regular_function(request):
        return "response"

    async def async_function(request):
        return "response"

    async def wrong_params(a, b):
        pass

    assert _is_asgi_app(regular_function) is False
    assert _is_asgi_app(async_function) is False
    assert _is_asgi_app(wrong_params) is False
    assert _is_asgi_app("not a function") is False


def test_fastapi_app():
    source = str(TEST_FUNCTIONS_DIR / "asgi_apps" / "fastapi_app.py")
    app = create_asgi_app(target="app", source=source)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

    response = client.get("/items/42")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42}


def test_bare_asgi_app():
    source = str(TEST_FUNCTIONS_DIR / "asgi_apps" / "bare_asgi.py")
    app = create_asgi_app(target="app", source=source)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Hello from ASGI"


def test_starlette_app():
    source = str(TEST_FUNCTIONS_DIR / "asgi_apps" / "starlette_app.py")
    app = create_asgi_app(target="app", source=source)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from Starlette"}


def test_error_handling_in_asgi_app():
    source = str(TEST_FUNCTIONS_DIR / "asgi_apps" / "fastapi_app.py")
    app = create_asgi_app(target="app", source=source)
    client = TestClient(app)

    response = client.get("/nonexistent")
    assert response.status_code == 404
