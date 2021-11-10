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

"""Function used to test handling functions using decorators."""
import flask

import functions_framework


@functions_framework.cloud_event
def function_cloud_event(cloud_event):
    """Test Event function that checks to see if a valid CloudEvent was sent.

    The function returns 200 if it received the expected event, otherwise 500.

    Args:
      cloud_event: A CloudEvent as defined by https://github.com/cloudevents/sdk-python.

    Returns:
      HTTP status code indicating whether valid event was sent or not.

    """
    valid_event = (
        cloud_event["id"] == "my-id"
        and cloud_event.data == {"name": "john"}
        and cloud_event["source"] == "from-galaxy-far-far-away"
        and cloud_event["type"] == "cloud_event.greet.you"
        and cloud_event["time"] == "2020-08-16T13:58:54.471765"
    )

    if not valid_event:
        flask.abort(500)


@functions_framework.http
def function_http(request):
    """Test function which returns the requested element of the HTTP request.

    Name of the requested HTTP request element is provided in the 'mode' field in
    the incoming JSON document.

    Args:
      request: The HTTP request which triggered this function. Must contain name
        of the requested HTTP request element in the 'mode' field in JSON document
        in request body.

    Returns:
      Value of the requested HTTP request element, or 'Bad Request' status in case
      of unrecognized incoming request.
    """
    mode = request.get_json().get("mode")
    if mode == "path":
        return request.path
    else:
        return "invalid request", 400
