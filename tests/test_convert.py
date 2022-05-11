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
import pretend
import pytest

from cloudevents.http import from_json, to_binary

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
            "publishTime": "2020-05-18T12:13:19Z",
            "messageId": "1215011316659232",
        },
    },
}


@pytest.fixture
def pubsub_cloud_event_output():
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
def raw_pubsub_request_noattributes():
    return {
        "subscription": "projects/sample-project/subscriptions/gcf-test-sub",
        "message": {"data": "eyJmb28iOiJiYXIifQ==", "messageId": "1215011316659232"},
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
def marshalled_pubsub_request_noattr():
    return {
        "data": {
            "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
            "data": "eyJmb28iOiJiYXIifQ==",
            "attributes": {},
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
def raw_pubsub_cloud_event_output(marshalled_pubsub_request):
    event = PUBSUB_CLOUD_EVENT.copy()
    # the data payload is more complex for the raw pubsub request
    data = marshalled_pubsub_request["data"]
    data["messageId"] = event["id"]
    data["publishTime"] = event["time"]
    event["data"] = {"message": data}
    return from_json(json.dumps(event))


@pytest.fixture
def firebase_auth_background_input():
    with open(TEST_DATA_DIR / "firebase-auth-legacy-input.json", "r") as f:
        return json.load(f)


@pytest.fixture
def firebase_auth_cloud_event_output():
    with open(TEST_DATA_DIR / "firebase-auth-cloud-event-output.json", "r") as f:
        return from_json(f.read())


@pytest.fixture
def firebase_db_background_input():
    with open(TEST_DATA_DIR / "firebase-db-legacy-input.json", "r") as f:
        return json.load(f)


@pytest.fixture
def firebase_db_cloud_event_output():
    with open(TEST_DATA_DIR / "firebase-db-cloud-event-output.json", "r") as f:
        return from_json(f.read())


@pytest.fixture
def create_ce_headers():
    return lambda event_type, source: {
        "ce-id": "my-id",
        "ce-type": event_type,
        "ce-source": source,
        "ce-specversion": "1.0",
        "ce-subject": "my/subject",
        "ce-time": "2020-08-16T13:58:54.471765",
    }


@pytest.mark.parametrize(
    "event", [PUBSUB_BACKGROUND_EVENT, PUBSUB_BACKGROUND_EVENT_WITHOUT_CONTEXT]
)
def test_pubsub_event_to_cloud_event(event, pubsub_cloud_event_output):
    req = flask.Request.from_values(json=event)
    cloud_event = event_conversion.background_event_to_cloud_event(req)
    assert cloud_event == pubsub_cloud_event_output


def test_firebase_auth_event_to_cloud_event(
    firebase_auth_background_input, firebase_auth_cloud_event_output
):
    req = flask.Request.from_values(json=firebase_auth_background_input)
    cloud_event = event_conversion.background_event_to_cloud_event(req)
    assert cloud_event == firebase_auth_cloud_event_output


def test_firebase_auth_event_to_cloud_event_no_metadata(
    firebase_auth_background_input, firebase_auth_cloud_event_output
):
    # Remove metadata from the events to verify conversion still works.
    del firebase_auth_background_input["data"]["metadata"]
    del firebase_auth_cloud_event_output.data["metadata"]

    req = flask.Request.from_values(json=firebase_auth_background_input)
    cloud_event = event_conversion.background_event_to_cloud_event(req)
    assert cloud_event == firebase_auth_cloud_event_output


def test_firebase_auth_event_to_cloud_event_no_metadata_timestamps(
    firebase_auth_background_input, firebase_auth_cloud_event_output
):
    # Remove metadata timestamps from the events to verify conversion still works.
    del firebase_auth_background_input["data"]["metadata"]["createdAt"]
    del firebase_auth_background_input["data"]["metadata"]["lastSignedInAt"]
    del firebase_auth_cloud_event_output.data["metadata"]["createTime"]
    del firebase_auth_cloud_event_output.data["metadata"]["lastSignInTime"]

    req = flask.Request.from_values(json=firebase_auth_background_input)
    cloud_event = event_conversion.background_event_to_cloud_event(req)
    assert cloud_event == firebase_auth_cloud_event_output


def test_firebase_auth_event_to_cloud_event_no_uid(
    firebase_auth_background_input, firebase_auth_cloud_event_output
):
    # Remove UIDs from the events to verify conversion still works. The UID is mapped
    # to the subject in the CloudEvent so remove that from the expected CloudEvent.
    del firebase_auth_background_input["data"]["uid"]
    del firebase_auth_cloud_event_output.data["uid"]
    del firebase_auth_cloud_event_output["subject"]

    req = flask.Request.from_values(json=firebase_auth_background_input)
    cloud_event = event_conversion.background_event_to_cloud_event(req)
    assert cloud_event == firebase_auth_cloud_event_output


def test_firebase_db_event_to_cloud_event_default_location(
    firebase_db_background_input, firebase_db_cloud_event_output
):
    req = flask.Request.from_values(json=firebase_db_background_input)
    cloud_event = event_conversion.background_event_to_cloud_event(req)
    assert cloud_event == firebase_db_cloud_event_output


def test_firebase_db_event_to_cloud_event_location_subdomain(
    firebase_db_background_input, firebase_db_cloud_event_output
):
    firebase_db_background_input["domain"] = "europe-west1.firebasedatabase.app"
    firebase_db_cloud_event_output["source"] = firebase_db_cloud_event_output[
        "source"
    ].replace("us-central1", "europe-west1")

    req = flask.Request.from_values(json=firebase_db_background_input)
    cloud_event = event_conversion.background_event_to_cloud_event(req)
    assert cloud_event == firebase_db_cloud_event_output


def test_firebase_db_event_to_cloud_event_missing_domain(
    firebase_db_background_input, firebase_db_cloud_event_output
):
    del firebase_db_background_input["domain"]
    req = flask.Request.from_values(json=firebase_db_background_input)

    with pytest.raises(EventConversionException) as exc_info:
        event_conversion.background_event_to_cloud_event(req)

    assert (
        "Invalid FirebaseDB event payload: missing 'domain'" in exc_info.value.args[0]
    )


def test_marshal_background_event_data_bad_request():
    req = pretend.stub(headers={}, get_json=lambda: None)

    with pytest.raises(EventConversionException):
        event_conversion.background_event_to_cloud_event(req)


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

    # Resource name is set to empty string when it cannot be parsed from the request path
    marshalled_pubsub_request["context"]["resource"]["name"] = ""

    assert payload == marshalled_pubsub_request


def test_marshal_background_event_data_without_topic_in_path_no_attr(
    raw_pubsub_request_noattributes, marshalled_pubsub_request_noattr
):
    req = flask.Request.from_values(
        json=raw_pubsub_request_noattributes, path="/myfunc/"
    )
    payload = event_conversion.marshal_background_event_data(req)

    # Remove timestamps as they get generates on the fly
    del marshalled_pubsub_request_noattr["context"]["timestamp"]
    del payload["context"]["timestamp"]

    # Resource name is set to empty string when it cannot be parsed from the request path
    marshalled_pubsub_request_noattr["context"]["resource"]["name"] = ""

    assert payload == marshalled_pubsub_request_noattr


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


@pytest.mark.parametrize(
    "request_fixture, overrides",
    [
        (
            "raw_pubsub_request",
            {
                "request_path": "x/projects/sample-project/topics/gcf-test?pubsub_trigger=true",
            },
        ),
        ("raw_pubsub_request", {"source": "//pubsub.googleapis.com/"}),
        ("marshalled_pubsub_request", {}),
    ],
)
def test_pubsub_emulator_request_to_cloud_event(
    raw_pubsub_cloud_event_output, request_fixture, overrides, request
):
    request_path = overrides.get("request_path", "/")
    payload = request.getfixturevalue(request_fixture)
    req = flask.Request.from_values(
        path=request_path,
        json=payload,
    )
    cloud_event = event_conversion.background_event_to_cloud_event(req)

    # Remove timestamps as they are generated on the fly.
    del raw_pubsub_cloud_event_output["time"]
    del raw_pubsub_cloud_event_output.data["message"]["publishTime"]
    del cloud_event["time"]
    del cloud_event.data["message"]["publishTime"]

    if "source" in overrides:
        # Default to the service name, when the topic is not configured subscription's pushEndpoint.
        raw_pubsub_cloud_event_output["source"] = overrides["source"]

    assert cloud_event == raw_pubsub_cloud_event_output


def test_pubsub_emulator_request_with_invalid_message(
    raw_pubsub_request, raw_pubsub_cloud_event_output
):
    # Create an invalid message payload
    raw_pubsub_request["message"] = None
    req = flask.Request.from_values(json=raw_pubsub_request, path="/")

    with pytest.raises(EventConversionException) as exc_info:
        cloud_event = event_conversion.background_event_to_cloud_event(req)
    assert "Failed to convert Pub/Sub payload to event" in exc_info.value.args[0]


@pytest.mark.parametrize(
    "ce_event_type, ce_source, expected_type, expected_resource",
    [
        (
            "google.firebase.database.ref.v1.written",
            "//firebasedatabase.googleapis.com/projects/_/instances/my-project-id",
            "providers/google.firebase.database/eventTypes/ref.write",
            "projects/_/instances/my-project-id/my/subject",
        ),
        (
            "google.cloud.pubsub.topic.v1.messagePublished",
            "//pubsub.googleapis.com/projects/sample-project/topics/gcf-test",
            "google.pubsub.topic.publish",
            {
                "service": "pubsub.googleapis.com",
                "name": "projects/sample-project/topics/gcf-test",
                "type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
            },
        ),
        (
            "google.cloud.storage.object.v1.finalized",
            "//storage.googleapis.com/projects/_/buckets/some-bucket",
            "google.storage.object.finalize",
            {
                "service": "storage.googleapis.com",
                "name": "projects/_/buckets/some-bucket/my/subject",
                "type": "value",
            },
        ),
        (
            "google.firebase.auth.user.v1.created",
            "//firebaseauth.googleapis.com/projects/my-project-id",
            "providers/firebase.auth/eventTypes/user.create",
            "projects/my-project-id",
        ),
        (
            "google.firebase.database.ref.v1.written",
            "//firebasedatabase.googleapis.com/projects/_/locations/us-central1/instances/my-project-id",
            "providers/google.firebase.database/eventTypes/ref.write",
            "projects/_/instances/my-project-id/my/subject",
        ),
        (
            "google.cloud.firestore.document.v1.written",
            "//firestore.googleapis.com/projects/project-id/databases/(default)",
            "providers/cloud.firestore/eventTypes/document.write",
            "projects/project-id/databases/(default)/my/subject",
        ),
    ],
)
def test_cloud_event_to_legacy_event(
    create_ce_headers,
    ce_event_type,
    ce_source,
    expected_type,
    expected_resource,
):
    headers = create_ce_headers(ce_event_type, ce_source)
    req = flask.Request.from_values(headers=headers, json={"kind": "value"})

    (res_data, res_context) = event_conversion.cloud_event_to_background_event(req)

    assert res_context.event_id == "my-id"
    assert res_context.timestamp == "2020-08-16T13:58:54.471765"
    assert res_context.event_type == expected_type
    assert res_context.resource == expected_resource
    assert res_data == {"kind": "value"}


def test_cloud_event_to_legacy_event_with_pubsub_message_payload(
    create_ce_headers,
):
    headers = create_ce_headers(
        "google.cloud.pubsub.topic.v1.messagePublished",
        "//pubsub.googleapis.com/projects/sample-project/topics/gcf-test",
    )
    data = {
        "message": {
            "data": "fizzbuzz",
            "messageId": "aaaaaa-1111-bbbb-2222-cccccccccccc",
            "publishTime": "2020-09-29T11:32:00.000Z",
        }
    }
    req = flask.Request.from_values(headers=headers, json=data)

    (res_data, res_context) = event_conversion.cloud_event_to_background_event(req)

    assert res_context.event_type == "google.pubsub.topic.publish"
    assert res_data == {"data": "fizzbuzz"}


def test_cloud_event_to_legacy_event_with_firebase_auth_ce(
    create_ce_headers,
):
    headers = create_ce_headers(
        "google.firebase.auth.user.v1.created",
        "//firebaseauth.googleapis.com/projects/my-project-id",
    )
    data = {
        "metadata": {
            "createTime": "2020-05-26T10:42:27Z",
            "lastSignInTime": "2020-10-24T11:00:00Z",
        },
        "uid": "my-id",
    }
    req = flask.Request.from_values(headers=headers, json=data)

    (res_data, res_context) = event_conversion.cloud_event_to_background_event(req)

    assert res_context.event_type == "providers/firebase.auth/eventTypes/user.create"
    assert res_data == {
        "metadata": {
            "createdAt": "2020-05-26T10:42:27Z",
            "lastSignedInAt": "2020-10-24T11:00:00Z",
        },
        "uid": "my-id",
    }


def test_cloud_event_to_legacy_event_with_firebase_auth_ce_empty_metadata(
    create_ce_headers,
):
    headers = create_ce_headers(
        "google.firebase.auth.user.v1.created",
        "//firebaseauth.googleapis.com/projects/my-project-id",
    )
    data = {"metadata": {}, "uid": "my-id"}
    req = flask.Request.from_values(headers=headers, json=data)

    (res_data, res_context) = event_conversion.cloud_event_to_background_event(req)

    assert res_context.event_type == "providers/firebase.auth/eventTypes/user.create"
    assert res_data == data


@pytest.mark.parametrize(
    "header_overrides, exception_message",
    [
        (
            {"ce-source": "invalid-source-format"},
            "Unexpected CloudEvent source",
        ),
        (
            {"ce-source": None},
            "Failed to convert CloudEvent to BackgroundEvent",
        ),
        (
            {"ce-subject": None},
            "Failed to convert CloudEvent to BackgroundEvent",
        ),
        (
            {"ce-type": "unknown-type"},
            "Unable to find background event equivalent type for",
        ),
    ],
)
def test_cloud_event_to_legacy_event_with_invalid_event(
    create_ce_headers,
    header_overrides,
    exception_message,
):
    headers = create_ce_headers(
        "google.firebase.database.ref.v1.written",
        "//firebasedatabase.googleapis.com/projects/_/instances/my-project-id",
    )
    for k, v in header_overrides.items():
        if v is None:
            del headers[k]
        else:
            headers[k] = v

    req = flask.Request.from_values(headers=headers, json={"some": "val"})

    with pytest.raises(EventConversionException) as exc_info:
        event_conversion.cloud_event_to_background_event(req)

    assert exception_message in exc_info.value.args[0]


@pytest.mark.parametrize(
    "source,expected_service,expected_name",
    [
        (
            "//firebasedatabase.googleapis.com/projects/_/instances/my-project-id",
            "firebasedatabase.googleapis.com",
            "projects/_/instances/my-project-id",
        ),
        (
            "//firebaseauth.googleapis.com/projects/my-project-id",
            "firebaseauth.googleapis.com",
            "projects/my-project-id",
        ),
        (
            "//firestore.googleapis.com/projects/project-id/databases/(default)",
            "firestore.googleapis.com",
            "projects/project-id/databases/(default)",
        ),
    ],
)
def test_split_ce_source(source, expected_service, expected_name):
    service, name = event_conversion._split_ce_source(source)
    assert service == expected_service
    assert name == expected_name
