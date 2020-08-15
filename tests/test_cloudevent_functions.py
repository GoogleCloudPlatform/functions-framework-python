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
def data_payload():
    return {"name": "john"}


@pytest.fixture
def json_decode_errmsg():
    return "could not json decode data payload"


@pytest.fixture
def missing_fields_errmsg():
    return "failed to find all required cloudevent fields"


@pytest.fixture
def cloudevent_1_0():
    attributes = {
        "specversion": "1.0",
        "id": "my-id",
        "source": "from-galaxy-far-far-away",
        "type": "cloudevent.greet.you",
    }
    data = {"name": "john"}
    return CloudEvent(attributes, data)


@pytest.fixture
def cloudevent_0_3():
    attributes = {
        "id": "my-id",
        "source": "from-galaxy-far-far-away",
        "type": "cloudevent.greet.you",
        "specversion": "0.3",
    }
    data = {"name": "john"}
    return CloudEvent(attributes, data)


@pytest.fixture
def create_headers_binary():
    return lambda specversion: {
        "ce-id": "my-id",
        "ce-source": "from-galaxy-far-far-away",
        "ce-type": "cloudevent.greet.you",
        "ce-specversion": specversion,
    }


@pytest.fixture
def create_structured_data():
    return lambda specversion: {
        "id": "my-id",
        "source": "from-galaxy-far-far-away",
        "type": "cloudevent.greet.you",
        "specversion": specversion,
    }


@pytest.fixture
def client():
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "main.py"
    target = "function"
    return create_app(target, source, "cloudevent").test_client()


@pytest.fixture
def empty_client():
    source = TEST_FUNCTIONS_DIR / "cloudevents" / "empty_data.py"
    target = "function"
    return create_app(target, source, "cloudevent").test_client()


def test_event(client, cloudevent_1_0):
    headers, data = to_structured_http(cloudevent_1_0)
    resp = client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_binary_event(client, cloudevent_1_0):
    headers, data = to_binary_http(cloudevent_1_0)
    resp = client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_event_0_3(client, cloudevent_0_3):
    headers, data = to_structured_http(cloudevent_0_3)
    resp = client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_binary_event_0_3(client, cloudevent_0_3):
    headers, data = to_binary_http(cloudevent_0_3)
    resp = client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


@pytest.mark.parametrize("specversion", ["0.3", "1.0"])
def test_cloudevent_missing_required_binary_fields(
    client, specversion, missing_fields_errmsg, create_headers_binary, data_payload
):
    headers = create_headers_binary(specversion)

    for remove_key in headers:
        invalid_headers = {key: headers[key] for key in headers if key != remove_key}
        resp = client.post("/", headers=invalid_headers, json=data_payload)

        assert resp.status_code == 400
        assert missing_fields_errmsg in resp.get_data().decode()


@pytest.mark.parametrize("specversion", ["0.3", "1.0"])
def test_cloudevent_missing_required_structured_fields(
    client, specversion, create_structured_data, missing_fields_errmsg
):
    headers = {"Content-Type": "application/cloudevents+json"}
    data = create_structured_data(specversion)

    for remove_key in data:
        invalid_data = {key: data[key] for key in data if key != remove_key}
        resp = client.post("/", headers=headers, json=invalid_data)

        assert resp.status_code == 400
        assert missing_fields_errmsg in resp.get_data().decode()


def test_invalid_fields_binary(
    client, create_headers_binary, missing_fields_errmsg, data_payload
):
    # Testing none specversion fails
    headers = create_headers_binary(None)
    resp = client.post("/", headers=headers, json=data_payload)

    assert resp.status_code == 400
    assert missing_fields_errmsg in resp.data.decode()


def test_unparsable_cloudevent(client, json_decode_errmsg):
    resp = client.post("/", headers={}, data="")

    assert resp.status_code == 400
    assert json_decode_errmsg in resp.data.decode()


@pytest.mark.parametrize("specversion", ["0.3", "1.0"])
def test_empty_data_binary(empty_client, create_headers_binary, specversion):
    headers = create_headers_binary(specversion)
    resp = empty_client.post("/", headers=headers, json="")

    assert resp.status_code == 200
    assert resp.get_data() == b"OK"


@pytest.mark.parametrize("specversion", ["0.3", "1.0"])
def test_empty_data_structured(empty_client, specversion, create_structured_data):
    headers = {"Content-Type": "application/cloudevents+json"}

    data = create_structured_data(specversion)
    resp = empty_client.post("/", headers=headers, json=data)

    assert resp.status_code == 200
    assert resp.get_data() == b"OK"


@pytest.mark.parametrize("specversion", ["0.3", "1.0"])
def test_no_mime_type_structured(empty_client, specversion, create_structured_data):
    data = create_structured_data(specversion)
    resp = empty_client.post("/", headers={}, json=data)

    assert resp.status_code == 200
    assert resp.get_data() == b"OK"
