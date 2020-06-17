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

"""Function used to test handling Cloud Event functions."""


def function(cloudevent):
    """Test Event function that checks to see if a valid CloudEvent was sent.

  The function returns 200 if it received the expected event, otherwise 500.

  Args:
    cloudevent: A Cloud event as defined by https://github.com/cloudevents/sdk-python.

  Returns:
    HTTP status code indicating whether valid event was sent or not.

  """
    valid_event = (
        cloudevent.EventID() == "my-id"
        and cloudevent.Data() == '{"name":"john"}'
        and cloudevent.Source() == "from-galaxy-far-far-away"
        and cloudevent.EventTime() == "tomorrow"
        and cloudevent.EventType() == "cloudevent.greet.you"
    )

    if valid_event:
        return 200
    else:
        return 500
