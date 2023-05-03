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

from cloudevents.http import CloudEvent, to_binary, to_structured

from functions_framework import create_app

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"
TEST_DATA_DIR = pathlib.Path(__file__).resolve().parent / "test_data"

# Python 3.5: ModuleNotFoundError does not exist
try:
    _ModuleNotFoundError = ModuleNotFoundError
except:
    _ModuleNotFoundError = ImportError


@pytest.fixture
def data_payload():
    return {"name": "john"}


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


@pytest.fixture
def cloud_event_0_3():
    attributes = {
        "id": "my-id",
        "source": "from-galaxy-far-far-away",
        "type": "cloud_event.greet.you",
        "specversion": "0.3",
        "time": "2020-08-16T13:58:54.471765",
    }
    data = {"name": "john"}
    return CloudEvent(attributes, data)


@pytest.fixture
def create_headers_binary():
    return lambda specversion: {
        "ce-id": "my-id",
        "ce-source": "from-galaxy-far-far-away",
        "ce-type": "cloud_event.greet.you",
        "ce-specversion": specversion,
        "time": "2020-08-16T13:58:54.471765",
    }


@pytest.fixture
def create_structured_data():
    return lambda specversion: {
        "id": "my-id",
        "source": "from-galaxy-far-far-away",
        "type": "cloud_event.greet.you",
        "specversion": specversion,
        "time": "2020-08-16T13:58:54.471765",
    }


@pytest.fixture
def background_event():
    with open(TEST_DATA_DIR / "pubsub_text-legacy-input.json", "r") as f:
        return json.load(f)


@pytest.fixture
def client():
    source = TEST_FUNCTIONS_DIR / "cloud_events" / "main.py"
    target = "function"
    return create_app(target, source, "cloudevent").test_client()


@pytest.fixture
def empty_client():
    source = TEST_FUNCTIONS_DIR / "cloud_events" / "empty_data.py"
    target = "function"
    return create_app(target, source, "cloudevent").test_client()


@pytest.fixture
def converted_background_event_client():
    source = TEST_FUNCTIONS_DIR / "cloud_events" / "converted_background_event.py"
    target = "function"
    return create_app(target, source, "cloudevent").test_client()


def test_event(client, cloud_event_1_0):
    headers, data = to_structured(cloud_event_1_0)
    resp = client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_binary_event(client, cloud_event_1_0):
    headers, data = to_binary(cloud_event_1_0)
    resp = client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_event_0_3(client, cloud_event_0_3):
    headers, data = to_structured(cloud_event_0_3)
    resp = client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_binary_event_0_3(client, cloud_event_0_3):
    headers, data = to_binary(cloud_event_0_3)
    resp = client.post("/", headers=headers, data=data)

    assert resp.status_code == 200
    assert resp.data == b"OK"


@pytest.mark.parametrize("specversion", ["0.3", "1.0"])
def test_cloud_event_missing_required_binary_fields(
    client, specversion, create_headers_binary, data_payload
):
    headers = create_headers_binary(specversion)

    for remove_key in headers:
        if remove_key == "time":
            continue

        invalid_headers = {key: headers[key] for key in headers if key != remove_key}
        resp = client.post("/", headers=invalid_headers, json=data_payload)

        assert resp.status_code == 400
        assert "MissingRequiredFields" in resp.get_data().decode()


@pytest.mark.parametrize("specversion", ["0.3", "1.0"])
def test_cloud_event_missing_required_structured_fields(
    client, specversion, create_structured_data
):
    headers = {"Content-Type": "application/cloudevents+json"}
    data = create_structured_data(specversion)

    for remove_key in data:
        if remove_key == "time":
            continue

        invalid_data = {key: data[key] for key in data if key != remove_key}
        resp = client.post("/", headers=headers, json=invalid_data)

        assert resp.status_code == 400
        assert "MissingRequiredFields" in resp.data.decode()


def test_invalid_fields_binary(client, create_headers_binary, data_payload):
    # Testing none specversion fails
    headers = create_headers_binary("not a spec version")
    resp = client.post("/", headers=headers, json=data_payload)

    assert resp.status_code == 400
    assert "InvalidRequiredFields" in resp.data.decode()


def test_unparsable_cloud_event(client):
    headers = {"Content-Type": "application/cloudevents+json"}
    resp = client.post("/", headers=headers, data="")

    assert resp.status_code == 400
    assert "Bad Request" in resp.data.decode()


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


def test_background_event(converted_background_event_client, background_event):
    resp = converted_background_event_client.post(
        "/", headers={}, json=background_event
    )

    assert resp.status_code == 200
    assert resp.get_data() == b"OK"
