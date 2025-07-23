# Copyright 2021 Google LLC
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
import sys

import pytest

from cloudevents import conversion as ce_conversion
from cloudevents.http import CloudEvent

import functions_framework._function_registry as registry

# Conditional import for Starlette
if sys.version_info >= (3, 8):
    from starlette.testclient import TestClient as StarletteTestClient
else:
    StarletteTestClient = None

from functions_framework import create_app

# Conditional import for async functionality
if sys.version_info >= (3, 8):
    from functions_framework.aio import create_asgi_app
else:
    create_asgi_app = None

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"


@pytest.fixture(autouse=True)
def clean_registries():
    """Clean up both REGISTRY_MAP and ASGI_FUNCTIONS registries."""
    original_registry_map = registry.REGISTRY_MAP.copy()
    original_asgi = registry.ASGI_FUNCTIONS.copy()
    registry.REGISTRY_MAP.clear()
    registry.ASGI_FUNCTIONS.clear()
    yield
    registry.REGISTRY_MAP.clear()
    registry.REGISTRY_MAP.update(original_registry_map)
    registry.ASGI_FUNCTIONS.clear()
    registry.ASGI_FUNCTIONS.update(original_asgi)


# Python 3.5: ModuleNotFoundError does not exist
try:
    _ModuleNotFoundError = ModuleNotFoundError
except:
    _ModuleNotFoundError = ImportError


@pytest.fixture(params=["decorator.py", "async_decorator.py"])
def cloud_event_decorator_client(request):
    source = TEST_FUNCTIONS_DIR / "decorators" / request.param
    target = "function_cloud_event"
    if not request.param.startswith("async_"):
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app)


@pytest.fixture(params=["decorator.py", "async_decorator.py"])
def http_decorator_client(request):
    source = TEST_FUNCTIONS_DIR / "decorators" / request.param
    target = "function_http"
    if not request.param.startswith("async_"):
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app)


@pytest.fixture
def cloud_event_1_0():
    attributes = {
        "specversion": "1.0",
        "id": "my-id",
        "source": "from-galaxy-far-far-away",
        "type": "cloud_event.greet.you",
        "time": "2020-08-16T13:58:54.471765",
    }
    data = {"name": "john"}
    return CloudEvent(attributes, data)


def test_cloud_event_decorator(cloud_event_decorator_client, cloud_event_1_0):
    headers, data = ce_conversion.to_structured(cloud_event_1_0)
    resp = cloud_event_decorator_client.post("/", headers=headers, data=data)
    assert resp.status_code == 200
    assert resp.text == "OK"


def test_http_decorator(http_decorator_client):
    resp = http_decorator_client.post("/my_path", json={"mode": "path"})
    assert resp.status_code == 200
    assert resp.text == "/my_path"


def test_aio_sync_cloud_event_decorator(cloud_event_1_0):
    """Test aio decorator with sync cloud event function."""
    source = TEST_FUNCTIONS_DIR / "decorators" / "async_decorator.py"
    target = "function_cloud_event_sync"

    app = create_asgi_app(target, source)
    client = StarletteTestClient(app)

    headers, data = ce_conversion.to_structured(cloud_event_1_0)
    resp = client.post("/", headers=headers, data=data)
    assert resp.status_code == 200
    assert resp.text == "OK"


def test_aio_sync_http_decorator():
    source = TEST_FUNCTIONS_DIR / "decorators" / "async_decorator.py"
    target = "function_http_sync"

    app = create_asgi_app(target, source)
    client = StarletteTestClient(app)

    resp = client.post("/my_path?mode=path")
    assert resp.status_code == 200
    assert resp.text == "/my_path"

    resp = client.post("/other_path")
    assert resp.status_code == 200
    assert resp.text == "sync response"


def test_aio_http_dict_response():
    source = TEST_FUNCTIONS_DIR / "decorators" / "async_decorator.py"
    target = "function_http_dict_response"

    app = create_asgi_app(target, source)
    client = StarletteTestClient(app)

    resp = client.post("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "hello", "count": 42, "success": True}


def test_aio_decorators_register_asgi_functions():
    """Test that @aio decorators add function names to ASGI_FUNCTIONS registry."""
    from functions_framework.aio import cloud_event, http

    @http
    async def test_http_func(request):
        return "test"

    @cloud_event
    async def test_cloud_event_func(event):
        pass

    assert "test_http_func" in registry.ASGI_FUNCTIONS
    assert "test_cloud_event_func" in registry.ASGI_FUNCTIONS

    assert registry.REGISTRY_MAP["test_http_func"] == "http"
    assert registry.REGISTRY_MAP["test_cloud_event_func"] == "cloudevent"

    @http
    def test_http_sync(request):
        return "sync"

    @cloud_event
    def test_cloud_event_sync(event):
        pass

    assert "test_http_sync" in registry.ASGI_FUNCTIONS
    assert "test_cloud_event_sync" in registry.ASGI_FUNCTIONS
