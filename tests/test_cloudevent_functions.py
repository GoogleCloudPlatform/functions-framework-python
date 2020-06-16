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

import cloudevents.sdk
import cloudevents.sdk.event.v1
import cloudevents.sdk.event.v03
import cloudevents.sdk.marshaller
import pytest

from functions_framework import LazyWSGIApp, create_app, exceptions

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"

# Python 3.5: ModuleNotFoundError does not exist
try:
    _ModuleNotFoundError = ModuleNotFoundError
except:
    _ModuleNotFoundError = ImportError


@pytest.fixture
def event_1_10():
    event = (
        cloudevents.sdk.event.v1.Event()
        .SetContentType("application/json")
        .SetData('{"name":"john"}')
        .SetEventID("my-id")
        .SetSource("from-galaxy-far-far-away")
        .SetEventTime("tomorrow")
        .SetEventType("cloudevent.greet.you")
    )
    return event


@pytest.fixture
def event_0_3():
    event = (
        cloudevents.sdk.event.v03.Event()
        .SetContentType("application/json")
        .SetData('{"name":"john"}')
        .SetEventID("my-id")
        .SetSource("from-galaxy-far-far-away")
        .SetEventTime("tomorrow")
        .SetEventType("cloudevent.greet.you")
    )
    return event


def test_event_1_0(event_1_10):
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "main.py"
    target = "function"

    client = create_app(target, source, "cloudevent").test_client()

    m = cloudevents.sdk.marshaller.NewDefaultHTTPMarshaller()
    structured_headers, structured_data = m.ToRequest(
        event_1_10, cloudevents.sdk.converters.TypeStructured, json.dumps
    )

    resp = client.post("/", headers=structured_headers, data=structured_data.getvalue())
    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_binary_event_1_0(event_1_10):
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "main.py"
    target = "function"

    client = create_app(target, source, "cloudevent").test_client()

    m = cloudevents.sdk.marshaller.NewDefaultHTTPMarshaller()

    binary_headers, binary_data = m.ToRequest(
        event_1_10, cloudevents.sdk.converters.TypeBinary, json.dumps
    )

    resp = client.post("/", headers=binary_headers, data=binary_data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_event_0_3(event_0_3):
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "main.py"
    target = "function"

    client = create_app(target, source, "cloudevent").test_client()

    m = cloudevents.sdk.marshaller.NewDefaultHTTPMarshaller()
    structured_headers, structured_data = m.ToRequest(
        event_0_3, cloudevents.sdk.converters.TypeStructured, json.dumps
    )

    resp = client.post("/", headers=structured_headers, data=structured_data.getvalue())
    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_non_cloud_event_():
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "main.py"
    target = "function"

    client = create_app(target, source, "cloudevent").test_client()

    resp = client.post("/", json="{not_event}")
    assert resp.status_code == 400
    assert resp.data != b"OK"
