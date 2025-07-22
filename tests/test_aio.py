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

from unittest.mock import Mock, call

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock

import pytest

from functions_framework import exceptions
from functions_framework.aio import (
    LazyASGIApp,
    _cloudevent_func_wrapper,
    _http_func_wrapper,
    create_asgi_app,
)

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"


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
