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

"""Function used to test handling CloudEvent functions."""
import flask


def function(cloudevent):
    """Test Event function that checks to see if the CloudEvent traceparent header is populated.

    The function returns 200 if it received the expected event, otherwise 500.

    Args:
        cloudevent: A CloudEvent as defined by https://github.com/cloudevents/sdk-python.

    Returns:
        HTTP status code indicating whether valid event was sent or not.
    """

    if not cloudevent["traceparent"]:
        flask.abort(500)