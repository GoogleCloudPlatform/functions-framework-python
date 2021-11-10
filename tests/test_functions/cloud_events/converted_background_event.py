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

"""Function used to test handling CloudEvent functions."""
import flask


def function(cloud_event):
    """Test event function that checks to see if a valid CloudEvent was sent.

    The function returns 200 if it received the expected event, otherwise 500.

    Args:
        cloud_event: A CloudEvent as defined by https://github.com/cloudevents/sdk-python.

    Returns:
        HTTP status code indicating whether valid event was sent or not.

    """
    data = {
        "message": {
            "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
            "attributes": {
                "attr1": "attr1-value",
            },
            "data": "dGVzdCBtZXNzYWdlIDM=",
            "messageId": "aaaaaa-1111-bbbb-2222-cccccccccccc",
            "publishTime": "2020-09-29T11:32:00.000Z",
        },
    }

    valid_event = (
        cloud_event["id"] == "aaaaaa-1111-bbbb-2222-cccccccccccc"
        and cloud_event.data == data
        and cloud_event["source"]
        == "//pubsub.googleapis.com/projects/sample-project/topics/gcf-test"
        and cloud_event["type"] == "google.cloud.pubsub.topic.v1.messagePublished"
        and cloud_event["time"] == "2020-09-29T11:32:00.000Z"
    )

    if not valid_event:
        flask.abort(500)
