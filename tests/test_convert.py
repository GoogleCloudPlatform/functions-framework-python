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
import json
import pathlib

import flask
import pytest

from cloudevents.http import from_json

from functions_framework import event_conversion
from functions_framework.exceptions import EventConversionException
from google.cloud.functions.context import Context

TEST_DATA_DIR = pathlib.Path(__file__).resolve().parent / "test_data"


PUBSUB_BACKGROUND_EVENT = {
    "context": {
        "eventId": "1215011316659232",
        "timestamp": "2020-05-18T12:13:19Z",
        "eventType": "google.pubsub.topic.publish",
        "resource": {
            "service": "pubsub.googleapis.com",
            "name": "projects/sample-project/topics/gcf-test",
            "type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        },
    },
    "data": {
        "data": "10",
    },
}

PUBSUB_BACKGROUND_EVENT_WITHOUT_CONTEXT = {
    "eventId": "1215011316659232",
    "timestamp": "2020-05-18T12:13:19Z",
    "eventType": "providers/cloud.pubsub/eventTypes/topic.publish",
    "resource": "projects/sample-project/topics/gcf-test",
    "data": {
        "data": "10",
    },
}

BACKGROUND_RESOURCE = {
    "service": "storage.googleapis.com",
    "name": "projects/_/buckets/some-bucket/objects/folder/Test.cs",
    "type": "storage#object",
}

BACKGROUND_RESOURCE_WITHOUT_SERVICE = {
    "name": "projects/_/buckets/some-bucket/objects/folder/Test.cs",
    "type": "storage#object",
}

BACKGROUND_RESOURCE_STRING = "projects/_/buckets/some-bucket/objects/folder/Test.cs"

PUBSUB_CLOUD_EVENT = {
    "specversion": "1.0",
    "id": "1215011316659232",
    "source": "//pubsub.googleapis.com/projects/sample-project/topics/gcf-test",
    "time": "2020-05-18T12:13:19Z",
    "type": "google.cloud.pubsub.topic.v1.messagePublished",
    "datacontenttype": "application/json",
    "data": {
        "message": {
            "data": "10",
        },
    },
}


@pytest.fixture
def pubsub_cloudevent_output():
    return from_json(json.dumps(PUBSUB_CLOUD_EVENT))


@pytest.fixture
def raw_pubsub_request():
    return {
        "subscription": "projects/sample-project/subscriptions/gcf-test-sub",
        "message": {
            "data": "eyJmb28iOiJiYXIifQ==",
            "messageId": "1215011316659232",
            "attributes": {"test": "123"},
        },
    }


@pytest.fixture
def marshalled_pubsub_request():
    return {
        "data": {
            "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
            "data": "eyJmb28iOiJiYXIifQ==",
            "attributes": {"test": "123"},
        },
        "context": {
            "eventId": "1215011316659232",
            "eventType": "google.pubsub.topic.publish",
            "resource": {
                "name": "projects/sample-project/topics/gcf-test",
                "service": "pubsub.googleapis.com",
                "type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
            },
            "timestamp": "2021-04-17T07:21:18.249Z",
        },
    }


@pytest.fixture
def raw_pubsub_cloudevent_output(marshalled_pubsub_request):
    event = PUBSUB_CLOUD_EVENT.copy()
    # the data payload is more complex for the raw pubsub request
    event["data"] = {"message": marshalled_pubsub_request["data"]}
    return from_json(json.dumps(event))


@pytest.fixture
def firebase_auth_background_input():
    with open(TEST_DATA_DIR / "firebase-auth-legacy-input.json", "r") as f:
        return json.load(f)


@pytest.fixture
def firebase_auth_cloudevent_output():
    with open(TEST_DATA_DIR / "firebase-auth-cloudevent-output.json", "r") as f:
        return from_json(f.read())


@pytest.mark.parametrize(
    "event", [PUBSUB_BACKGROUND_EVENT, PUBSUB_BACKGROUND_EVENT_WITHOUT_CONTEXT]
)
def test_pubsub_event_to_cloudevent(event, pubsub_cloudevent_output):
    req = flask.Request.from_values(json=event)
    cloudevent = event_conversion.background_event_to_cloudevent(req)
    assert cloudevent == pubsub_cloudevent_output


def test_firebase_auth_event_to_cloudevent(
    firebase_auth_background_input, firebase_auth_cloudevent_output
):
    req = flask.Request.from_values(json=firebase_auth_background_input)
    cloudevent = event_conversion.background_event_to_cloudevent(req)
    assert cloudevent == firebase_auth_cloudevent_output


def test_firebase_auth_event_to_cloudevent_no_metadata(
    firebase_auth_background_input, firebase_auth_cloudevent_output
):
    # Remove metadata from the events to verify conversion still works.
    del firebase_auth_background_input["data"]["metadata"]
    del firebase_auth_cloudevent_output.data["metadata"]

    req = flask.Request.from_values(json=firebase_auth_background_input)
    cloudevent = event_conversion.background_event_to_cloudevent(req)
    assert cloudevent == firebase_auth_cloudevent_output


def test_firebase_auth_event_to_cloudevent_no_metadata_timestamps(
    firebase_auth_background_input, firebase_auth_cloudevent_output
):
    # Remove metadata timestamps from the events to verify conversion still works.
    del firebase_auth_background_input["data"]["metadata"]["createdAt"]
    del firebase_auth_background_input["data"]["metadata"]["lastSignedInAt"]
    del firebase_auth_cloudevent_output.data["metadata"]["createTime"]
    del firebase_auth_cloudevent_output.data["metadata"]["lastSignInTime"]

    req = flask.Request.from_values(json=firebase_auth_background_input)
    cloudevent = event_conversion.background_event_to_cloudevent(req)
    assert cloudevent == firebase_auth_cloudevent_output


def test_firebase_auth_event_to_cloudevent_no_uid(
    firebase_auth_background_input, firebase_auth_cloudevent_output
):
    # Remove UIDs from the events to verify conversion still works. The UID is mapped
    # to the subject in the CloudEvent so remove that from the expected CloudEvent.
    del firebase_auth_background_input["data"]["uid"]
    del firebase_auth_cloudevent_output.data["uid"]
    del firebase_auth_cloudevent_output["subject"]

    req = flask.Request.from_values(json=firebase_auth_background_input)
    cloudevent = event_conversion.background_event_to_cloudevent(req)
    assert cloudevent == firebase_auth_cloudevent_output


@pytest.mark.parametrize(
    "background_resource",
    [
        BACKGROUND_RESOURCE,
        BACKGROUND_RESOURCE_WITHOUT_SERVICE,
        BACKGROUND_RESOURCE_STRING,
    ],
)
def test_split_resource(background_resource):
    context = Context(
        eventType="google.storage.object.finalize", resource=background_resource
    )
    service, resource, subject = event_conversion._split_resource(context)
    assert service == "storage.googleapis.com"
    assert resource == "projects/_/buckets/some-bucket"
    assert subject == "objects/folder/Test.cs"


def test_split_resource_unknown_service_and_event_type():
    # With both an unknown service and an unknown event type, we won't attempt any
    # event type mapping or resource/subject splitting.
    background_resource = {
        "service": "not_a_known_service",
        "name": "projects/_/my/stuff/at/test.txt",
        "type": "storage#object",
    }
    context = Context(eventType="not_a_known_event_type", resource=background_resource)
    service, resource, subject = event_conversion._split_resource(context)
    assert service == "not_a_known_service"
    assert resource == "projects/_/my/stuff/at/test.txt"
    assert subject == ""


def test_split_resource_without_service_unknown_event_type():
    background_resource = {
        "name": "projects/_/buckets/some-bucket/objects/folder/Test.cs",
        "type": "storage#object",
    }
    # This event type cannot be mapped to an equivalent CloudEvent type.
    context = Context(eventType="not_a_known_event_type", resource=background_resource)
    with pytest.raises(EventConversionException) as exc_info:
        event_conversion._split_resource(context)
    assert "Unable to find CloudEvent equivalent service" in exc_info.value.args[0]


def test_split_resource_no_resource_regex_match():
    background_resource = {
        "service": "storage.googleapis.com",
        # This name will not match the regex associated with the service.
        "name": "foo/bar/baz",
        "type": "storage#object",
    }
    context = Context(
        eventType="google.storage.object.finalize", resource=background_resource
    )
    with pytest.raises(EventConversionException) as exc_info:
        event_conversion._split_resource(context)
    assert "Resource regex did not match" in exc_info.value.args[0]


def test_marshal_background_event_data_without_topic_in_path(
    raw_pubsub_request, marshalled_pubsub_request
):
    req = flask.Request.from_values(json=raw_pubsub_request, path="/myfunc/")
    payload = event_conversion.marshal_background_event_data(req)

    # Remove timestamps as they get generates on the fly
    del marshalled_pubsub_request["context"]["timestamp"]
    del payload["context"]["timestamp"]

    # Resource name is set to None when it cannot be parsed from the request path
    marshalled_pubsub_request["context"]["resource"]["name"] = None

    assert payload == marshalled_pubsub_request


def test_marshal_background_event_data_with_topic_path(
    raw_pubsub_request, marshalled_pubsub_request
):
    req = flask.Request.from_values(
        json=raw_pubsub_request,
        path="x/projects/sample-project/topics/gcf-test?pubsub_trigger=true",
    )
    payload = event_conversion.marshal_background_event_data(req)

    # Remove timestamps as they are generated on the fly.
    del marshalled_pubsub_request["context"]["timestamp"]
    del payload["context"]["timestamp"]

    assert payload == marshalled_pubsub_request


def test_pubsub_emulator_request_to_cloudevent(
    raw_pubsub_request, raw_pubsub_cloudevent_output
):
    req = flask.Request.from_values(
        json=raw_pubsub_request,
        path="x/projects/sample-project/topics/gcf-test?pubsub_trigger=true",
    )
    cloudevent = event_conversion.background_event_to_cloudevent(req)

    # Remove timestamps as they are generated on the fly.
    del raw_pubsub_cloudevent_output["time"]
    del cloudevent["time"]

    assert cloudevent == raw_pubsub_cloudevent_output


def test_pubsub_emulator_request_to_cloudevent_without_topic_path(
    raw_pubsub_request, raw_pubsub_cloudevent_output
):
    req = flask.Request.from_values(json=raw_pubsub_request, path="/")
    cloudevent = event_conversion.background_event_to_cloudevent(req)

    # Remove timestamps as they are generated on the fly.
    del raw_pubsub_cloudevent_output["time"]
    del cloudevent["time"]

    # Default to the service name, when the topic is not configured subscription's pushEndpoint.
    raw_pubsub_cloudevent_output["source"] = "//pubsub.googleapis.com/"

    assert cloudevent == raw_pubsub_cloudevent_output
