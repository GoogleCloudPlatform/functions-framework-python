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
import json
import pathlib

import pytest

from cloudevents.http import CloudEvent, from_http, to_binary_http, to_structured_http

from functions_framework import LazyWSGIApp, create_app, exceptions

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"

# Python 3.5: ModuleNotFoundError does not exist
try:
    _ModuleNotFoundError = ModuleNotFoundError
except:
    _ModuleNotFoundError = ImportError


@pytest.fixture
def cloudevent_1_0():
    attributes = {
        "Content-Type": "application/json",
        "id": "my-id",
        "source": "from-galaxy-far-far-away",
        "time": "tomorrow",
        "type": "cloudevent.greet.you",
    }
    data = {"name": "john"}
    return CloudEvent(attributes, data)


@pytest.fixture
def cloudevent_0_3():
    attributes = {
        "Content-Type": "application/json",
        "id": "my-id",
        "source": "from-galaxy-far-far-away",
        "time": "tomorrow",
        "type": "cloudevent.greet.you",
        "specversion": "0.3",
    }
    data = {"name": "john"}
    return CloudEvent(attributes, data)


def test_event_1_0(cloudevent_1_0):
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "main.py"
    target = "function"

    client = create_app(target, source, "cloudevent").test_client()
    headers, data = to_structured_http(cloudevent_1_0)

    resp = client.post("/", headers=headers, data=data)
    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_binary_event_1_0(cloudevent_1_0):
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "main.py"
    target = "function"

    client = create_app(target, source, "cloudevent").test_client()

    headers, data = to_binary_http(cloudevent_1_0)

    resp = client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_event_0_3(cloudevent_0_3):
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "main.py"
    target = "function"

    client = create_app(target, source, "cloudevent").test_client()

    headers, data = to_structured_http(cloudevent_0_3)

    resp = client.post("/", headers=headers, data=data)
    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_invalid_cloudevent():
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "main.py"
    target = "function"

    client = create_app(target, source, "cloudevent").test_client()

    resp = client.post("/", headers={}, data="data")
    assert resp.status_code == 400
