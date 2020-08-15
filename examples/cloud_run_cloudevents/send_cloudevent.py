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
from cloudevents.http import CloudEvent, to_structured_http
import requests
import json


# CloudEvent constructor minimally requires a source and type field
attributes = {
    "Content-Type": "application/json",
    "source": "from-galaxy-far-far-away",
    "type": "cloudevent.greet.you"
}
data = {"name":"john"}

event = CloudEvent(attributes, data)

# Send event
headers, data = to_structured_http(event)
response = requests.post("http://localhost:8080/", headers=headers, data=data)
