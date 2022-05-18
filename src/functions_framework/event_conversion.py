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
import re

from datetime import datetime
from typing import Any, Optional, Tuple

from cloudevents.exceptions import MissingRequiredFields
from cloudevents.http import CloudEvent, from_http, is_binary

from functions_framework.background_event import BackgroundEvent
from functions_framework.exceptions import EventConversionException
from google.cloud.functions.context import Context

_CLOUD_EVENT_SPEC_VERSION = "1.0"

# Maps background/legacy event types to their equivalent CloudEvent types.
# For more info on event mappings see
# https://github.com/GoogleCloudPlatform/functions-framework-conformance/blob/master/docs/mapping.md
_BACKGROUND_TO_CE_TYPE = {
    "google.pubsub.topic.publish": "google.cloud.pubsub.topic.v1.messagePublished",
    "providers/cloud.pubsub/eventTypes/topic.publish": "google.cloud.pubsub.topic.v1.messagePublished",
    "google.storage.object.finalize": "google.cloud.storage.object.v1.finalized",
    "google.storage.object.delete": "google.cloud.storage.object.v1.deleted",
    "google.storage.object.archive": "google.cloud.storage.object.v1.archived",
    "google.storage.object.metadataUpdate": "google.cloud.storage.object.v1.metadataUpdated",
    "providers/cloud.firestore/eventTypes/document.write": "google.cloud.firestore.document.v1.written",
    "providers/cloud.firestore/eventTypes/document.create": "google.cloud.firestore.document.v1.created",
    "providers/cloud.firestore/eventTypes/document.update": "google.cloud.firestore.document.v1.updated",
    "providers/cloud.firestore/eventTypes/document.delete": "google.cloud.firestore.document.v1.deleted",
    "providers/firebase.auth/eventTypes/user.create": "google.firebase.auth.user.v1.created",
    "providers/firebase.auth/eventTypes/user.delete": "google.firebase.auth.user.v1.deleted",
    "providers/google.firebase.analytics/eventTypes/event.log": "google.firebase.analytics.log.v1.written",
    "providers/google.firebase.database/eventTypes/ref.create": "google.firebase.database.ref.v1.created",
    "providers/google.firebase.database/eventTypes/ref.write": "google.firebase.database.ref.v1.written",
    "providers/google.firebase.database/eventTypes/ref.update": "google.firebase.database.ref.v1.updated",
    "providers/google.firebase.database/eventTypes/ref.delete": "google.firebase.database.ref.v1.deleted",
    "providers/cloud.storage/eventTypes/object.change": "google.cloud.storage.object.v1.finalized",
}

# _BACKGROUND_TO_CE_TYPE contains duplicate values for some keys. This set contains the duplicates
# that should be dropped when generating the inverse mapping _CE_TO_BACKGROUND_TYPE
_NONINVERTALBE_CE_TYPES = {
    "providers/cloud.pubsub/eventTypes/topic.publish",
    "providers/cloud.storage/eventTypes/object.change",
}

# Maps CloudEvent types to the equivalent background/legacy event types (inverse
# of _BACKGROUND_TO_CE_TYPE)
_CE_TO_BACKGROUND_TYPE = {
    v: k for k, v in _BACKGROUND_TO_CE_TYPE.items() if k not in _NONINVERTALBE_CE_TYPES
}

# CloudEvent service names.
_FIREBASE_AUTH_CE_SERVICE = "firebaseauth.googleapis.com"
_FIREBASE_CE_SERVICE = "firebase.googleapis.com"
_FIREBASE_DB_CE_SERVICE = "firebasedatabase.googleapis.com"
_FIRESTORE_CE_SERVICE = "firestore.googleapis.com"
_PUBSUB_CE_SERVICE = "pubsub.googleapis.com"
_STORAGE_CE_SERVICE = "storage.googleapis.com"

# Raw pubsub types
_PUBSUB_EVENT_TYPE = "google.pubsub.topic.publish"
_PUBSUB_MESSAGE_TYPE = "type.googleapis.com/google.pubsub.v1.PubsubMessage"

_PUBSUB_TOPIC_REQUEST_PATH = re.compile(r"projects\/[^/?]+\/topics\/[^/?]+")

# Maps background event services to their equivalent CloudEvent services.
_SERVICE_BACKGROUND_TO_CE = {
    "providers/cloud.firestore/": _FIRESTORE_CE_SERVICE,
    "providers/google.firebase.analytics/": _FIREBASE_CE_SERVICE,
    "providers/firebase.auth/": _FIREBASE_AUTH_CE_SERVICE,
    "providers/google.firebase.database/": _FIREBASE_DB_CE_SERVICE,
    "providers/cloud.pubsub/": _PUBSUB_CE_SERVICE,
    "providers/cloud.storage/": _STORAGE_CE_SERVICE,
    "google.pubsub": _PUBSUB_CE_SERVICE,
    "google.storage": _STORAGE_CE_SERVICE,
}

# Maps CloudEvent service strings to regular expressions used to split a background
# event resource string into CloudEvent resource and subject strings. Each regex
# must have exactly two capture groups: the first for the resource and the second
# for the subject.
_CE_SERVICE_TO_RESOURCE_RE = {
    _FIREBASE_CE_SERVICE: re.compile(r"^(projects/[^/]+)/(events/[^/]+)$"),
    _FIREBASE_DB_CE_SERVICE: re.compile(r"^projects/_/(instances/[^/]+)/(refs/.+)$"),
    _FIRESTORE_CE_SERVICE: re.compile(
        r"^(projects/[^/]+/databases/\(default\))/(documents/.+)$"
    ),
    _STORAGE_CE_SERVICE: re.compile(r"^(projects/[^/]/buckets/[^/]+)/(objects/.+)$"),
}

# Maps Firebase Auth background event metadata field names to their equivalent
# CloudEvent field names.
_FIREBASE_AUTH_METADATA_FIELDS_BACKGROUND_TO_CE = {
    "createdAt": "createTime",
    "lastSignedInAt": "lastSignInTime",
}
# Maps Firebase Auth CloudEvent metadata field names to their equivalent
# background event field names (inverse of _FIREBASE_AUTH_METADATA_FIELDS_BACKGROUND_TO_CE).
_FIREBASE_AUTH_METADATA_FIELDS_CE_TO_BACKGROUND = {
    v: k for k, v in _FIREBASE_AUTH_METADATA_FIELDS_BACKGROUND_TO_CE.items()
}


def background_event_to_cloud_event(request) -> CloudEvent:
    """Converts a background event represented by the given HTTP request into a CloudEvent."""
    event_data = marshal_background_event_data(request)
    if not event_data:
        raise EventConversionException("Failed to parse JSON")

    event_object = BackgroundEvent(**event_data)
    data = event_object.data
    context = Context(**event_object.context)

    if context.event_type not in _BACKGROUND_TO_CE_TYPE:
        raise EventConversionException(
            f'Unable to find CloudEvent equivalent type for "{context.event_type}"'
        )
    new_type = _BACKGROUND_TO_CE_TYPE[context.event_type]

    service, resource, subject = _split_resource(context)
    source = f"//{service}/{resource}"

    # Handle Pub/Sub events.
    if service == _PUBSUB_CE_SERVICE:
        if "messageId" not in data:
            data["messageId"] = context.event_id
        if "publishTime" not in data:
            data["publishTime"] = context.timestamp
        data = {"message": data}

    # Handle Firebase Auth events.
    if service == _FIREBASE_AUTH_CE_SERVICE:
        if "metadata" in data:
            for old, new in _FIREBASE_AUTH_METADATA_FIELDS_BACKGROUND_TO_CE.items():
                if old in data["metadata"]:
                    data["metadata"][new] = data["metadata"][old]
                    del data["metadata"][old]
        if "uid" in data:
            uid = data["uid"]
            subject = f"users/{uid}"

    # Handle Firebase DB events.
    if service == _FIREBASE_DB_CE_SERVICE:
        # The CE source of firebasedatabase CloudEvents includes location information
        # that is inferred from the 'domain' field of legacy events.
        if "domain" not in event_data:
            raise EventConversionException(
                "Invalid FirebaseDB event payload: missing 'domain'"
            )

        domain = event_data["domain"]
        location = "us-central1"
        if domain != "firebaseio.com":
            location = domain.split(".")[0]

        resource = f"projects/_/locations/{location}/{resource}"
        source = f"//{service}/{resource}"

    metadata = {
        "id": context.event_id,
        "time": context.timestamp,
        "specversion": _CLOUD_EVENT_SPEC_VERSION,
        "datacontenttype": "application/json",
        "type": new_type,
        "source": source,
    }

    if subject:
        metadata["subject"] = subject

    return CloudEvent(metadata, data)


def is_convertable_cloud_event(request) -> bool:
    """Is the given request a known CloudEvent that can be converted to background event."""
    if is_binary(request.headers):
        event_type = request.headers.get("ce-type")
        event_source = request.headers.get("ce-source")
        return (
            event_source is not None
            and event_type is not None
            and event_type in _CE_TO_BACKGROUND_TYPE
        )
    return False


def _split_ce_source(source) -> Tuple[str, str]:
    """Splits a CloudEvent source string into resource and subject components."""
    regex = re.compile(r"\/\/([^/]+)\/(.+)")
    match = regex.fullmatch(source)
    if not match:
        raise EventConversionException("Unexpected CloudEvent source.")

    return match.group(1), match.group(2)


def cloud_event_to_background_event(request) -> Tuple[Any, Context]:
    """Converts a background event represented by the given HTTP request into a CloudEvent."""
    try:
        event = from_http(request.headers, request.get_data())
        data = event.data
        service, name = _split_ce_source(event["source"])

        if event["type"] not in _CE_TO_BACKGROUND_TYPE:
            raise EventConversionException(
                f'Unable to find background event equivalent type for "{event["type"]}"'
            )

        if service == _PUBSUB_CE_SERVICE:
            resource = {"service": service, "name": name, "type": _PUBSUB_MESSAGE_TYPE}
            if "message" in data:
                data = data["message"]
            if "messageId" in data:
                del data["messageId"]
            if "publishTime" in data:
                del data["publishTime"]
        elif service == _FIREBASE_AUTH_CE_SERVICE:
            resource = name
            if "metadata" in data:
                for old, new in _FIREBASE_AUTH_METADATA_FIELDS_CE_TO_BACKGROUND.items():
                    if old in data["metadata"]:
                        data["metadata"][new] = data["metadata"][old]
                        del data["metadata"][old]
        elif service == _STORAGE_CE_SERVICE:
            resource = {
                "name": f"{name}/{event['subject']}",
                "service": service,
                "type": data["kind"],
            }
        elif service == _FIREBASE_DB_CE_SERVICE:
            name = re.sub("/locations/[^/]+", "", name)
            resource = f"{name}/{event['subject']}"
        else:
            resource = f"{name}/{event['subject']}"

        context = Context(
            eventId=event["id"],
            timestamp=event["time"],
            eventType=_CE_TO_BACKGROUND_TYPE[event["type"]],
            resource=resource,
        )
        return (data, context)
    except (AttributeError, KeyError, TypeError, MissingRequiredFields):
        raise EventConversionException(
            "Failed to convert CloudEvent to BackgroundEvent."
        )


def _split_resource(context: Context) -> Tuple[str, str, str]:
    """Splits a background event's resource into a CloudEvent service, resource, and subject."""
    service = ""
    resource = ""
    if isinstance(context.resource, dict):
        service = context.resource.get("service", "")
        resource = context.resource["name"]
    else:
        resource = context.resource

    # If there's no service we'll choose an appropriate one based on the event type.
    if not service:
        for b_service, ce_service in _SERVICE_BACKGROUND_TO_CE.items():
            if context.event_type.startswith(b_service):
                service = ce_service
                break
        if not service:
            raise EventConversionException(
                "Unable to find CloudEvent equivalent service "
                f"for {context.event_type}"
            )

    # If we don't need to split the resource string then we're done.
    if service not in _CE_SERVICE_TO_RESOURCE_RE:
        return service, resource, ""

    # Split resource into resource and subject.
    match = _CE_SERVICE_TO_RESOURCE_RE[service].fullmatch(resource)
    if not match:
        raise EventConversionException("Resource regex did not match")

    return service, match.group(1), match.group(2)


def marshal_background_event_data(request):
    """Marshal the request body of a raw Pub/Sub HTTP request into the schema that is expected of
    a background event"""
    try:
        request_data = request.get_json()
        if not _is_raw_pubsub_payload(request_data):
            # If this in not a raw Pub/Sub request, return the unaltered request data.
            return request_data
        return {
            "context": {
                "eventId": request_data["message"]["messageId"],
                "timestamp": request_data["message"].get(
                    "publishTime", datetime.utcnow().isoformat() + "Z"
                ),
                "eventType": _PUBSUB_EVENT_TYPE,
                "resource": {
                    "service": _PUBSUB_CE_SERVICE,
                    "type": _PUBSUB_MESSAGE_TYPE,
                    "name": _parse_pubsub_topic(request.path),
                },
            },
            "data": {
                "@type": _PUBSUB_MESSAGE_TYPE,
                "data": request_data["message"]["data"],
                "attributes": request_data["message"].get("attributes", {}),
            },
        }
    except (AttributeError, KeyError, TypeError):
        raise EventConversionException("Failed to convert Pub/Sub payload to event")


def _is_raw_pubsub_payload(request_data) -> bool:
    """Does the given request body match the schema of a unmarshalled Pub/Sub request"""
    return (
        request_data is not None
        and "context" not in request_data
        and "subscription" in request_data
        and "message" in request_data
        and "data" in request_data["message"]
        and "messageId" in request_data["message"]
    )


def _parse_pubsub_topic(request_path) -> Optional[str]:
    match = _PUBSUB_TOPIC_REQUEST_PATH.search(request_path)
    if match:
        return match.group(0)
    else:
        # It is possible to configure a Pub/Sub subscription to push directly to this function
        # without passing the topic name in the URL path.
        return ""
