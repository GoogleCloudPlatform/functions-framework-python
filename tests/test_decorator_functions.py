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

import pytest

from cloudevents.http import CloudEvent, to_binary, to_structured

from functions_framework import create_app

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"

# Python 3.5: ModuleNotFoundError does not exist
try:
    _ModuleNotFoundError = ModuleNotFoundError
except:
    _ModuleNotFoundError = ImportError


@pytest.fixture
def cloud_event_decorator_client():
    source = TEST_FUNCTIONS_DIR / "decorators" / "decorator.py"
    target = "function_cloud_event"
    return create_app(target, source).test_client()


@pytest.fixture
def http_decorator_client():
    source = TEST_FUNCTIONS_DIR / "decorators" / "decorator.py"
    target = "function_http"
    return create_app(target, source).test_client()


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
    headers, data = to_structured(cloud_event_1_0)
    resp = cloud_event_decorator_client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_http_decorator(http_decorator_client):
    resp = http_decorator_client.post("/my_path", json={"mode": "path"})
    assert resp.status_code == 200
    assert resp.data == b"/my_path"
