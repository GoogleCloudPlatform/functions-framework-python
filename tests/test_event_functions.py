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
import re

import cloudevents.sdk
import cloudevents.sdk.event.v1
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
def background_json(tmpdir):
    return {
        "context": {
            "eventId": "some-eventId",
            "timestamp": "some-timestamp",
            "eventType": "some-eventType",
            "resource": "some-resource",
        },
        "data": {"filename": str(tmpdir / "filename.txt"), "value": "some-value"},
    }


def test_non_legacy_event_fails():
    cloud_event = (
        cloudevents.sdk.event.v1.Event()
        .SetContentType("application/json")
        .SetData('{"name":"john"}')
        .SetEventID("my-id")
        .SetSource("from-galaxy-far-far-away")
        .SetEventTime("tomorrow")
        .SetEventType("cloudevent.greet.you")
    )
    m = cloudevents.sdk.marshaller.NewDefaultHTTPMarshaller()
    structured_headers, structured_data = m.ToRequest(
        cloud_event, cloudevents.sdk.converters.TypeStructured, json.dumps
    )

    source = TEST_FUNCTIONS_DIR / "background_trigger" / "main.py"
    target = "function"

    client = create_app(target, source, "event").test_client()
    resp = client.post("/", headers=structured_headers, data=structured_data.getvalue())
    assert resp.status_code == 400
    assert resp.data != b"OK"


def test_background_function_executes(background_json):
    source = TEST_FUNCTIONS_DIR / "background_trigger" / "main.py"
    target = "function"

    client = create_app(target, source, "event").test_client()

    resp = client.post("/", json=background_json)
    assert resp.status_code == 200


def test_background_function_supports_get(background_json):
    source = TEST_FUNCTIONS_DIR / "background_trigger" / "main.py"
    target = "function"

    client = create_app(target, source, "event").test_client()

    resp = client.get("/")
    assert resp.status_code == 200


def test_background_function_executes_entry_point_one(background_json):
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "myFunctionFoo"

    client = create_app(target, source, "event").test_client()

    resp = client.post("/", json=background_json)
    assert resp.status_code == 200


def test_background_function_executes_entry_point_two(background_json):
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "myFunctionBar"

    client = create_app(target, source, "event").test_client()

    resp = client.post("/", json=background_json)
    assert resp.status_code == 200


def test_multiple_calls(background_json):
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "myFunctionFoo"

    client = create_app(target, source, "event").test_client()

    resp = client.post("/", json=background_json)
    assert resp.status_code == 200
    resp = client.post("/", json=background_json)
    assert resp.status_code == 200
    resp = client.post("/", json=background_json)
    assert resp.status_code == 200


def test_pubsub_payload(background_json):
    source = TEST_FUNCTIONS_DIR / "background_trigger" / "main.py"
    target = "function"

    client = create_app(target, source, "event").test_client()

    resp = client.post("/", json=background_json)

    assert resp.status_code == 200
    assert resp.data == b"OK"

    with open(background_json["data"]["filename"]) as f:
        assert f.read() == '{{"entryPoint": "function", "value": "{}"}}'.format(
            background_json["data"]["value"]
        )


def test_background_function_no_data(background_json):
    source = TEST_FUNCTIONS_DIR / "background_trigger" / "main.py"
    target = "function"

    client = create_app(target, source, "event").test_client()

    resp = client.post("/")
    assert resp.status_code == 400


def test_invalid_function_definition_multiple_entry_points():
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "function"

    with pytest.raises(exceptions.MissingTargetException) as excinfo:
        create_app(target, source, "event")

    assert re.match(
        "File .* is expected to contain a function named function", str(excinfo.value)
    )


def test_invalid_function_definition_multiple_entry_points_invalid_function():
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "invalidFunction"

    with pytest.raises(exceptions.MissingTargetException) as excinfo:
        create_app(target, source, "event")

    assert re.match(
        "File .* is expected to contain a function named invalidFunction",
        str(excinfo.value),
    )


def test_invalid_function_definition_multiple_entry_points_not_a_function():
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "notAFunction"

    with pytest.raises(exceptions.InvalidTargetTypeException) as excinfo:
        create_app(target, source, "event")

    assert re.match(
        "The function defined in file .* as notAFunction needs to be of type "
        "function. Got: .*",
        str(excinfo.value),
    )


def test_invalid_function_definition_function_syntax_error():
    source = TEST_FUNCTIONS_DIR / "background_load_error" / "main.py"
    target = "function"

    with pytest.raises(SyntaxError) as excinfo:
        create_app(target, source, "event")

    assert any(
        (
            "invalid syntax" in str(excinfo.value),  # Python <3.8
            "unmatched ')'" in str(excinfo.value),  # Python >3.8
        )
    )


def test_invalid_function_definition_missing_dependency():
    source = TEST_FUNCTIONS_DIR / "background_missing_dependency" / "main.py"
    target = "function"

    with pytest.raises(_ModuleNotFoundError) as excinfo:
        create_app(target, source, "event")

    assert "No module named 'nonexistentpackage'" in str(excinfo.value)
