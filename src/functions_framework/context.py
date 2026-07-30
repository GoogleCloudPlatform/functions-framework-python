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

"""Definition of the context type used by Cloud Functions in Python."""


class Context(object):
    """Context passed to background functions."""

    def __init__(self, eventId="", timestamp="", eventType="", resource=""):
        self.event_id = eventId
        self.timestamp = timestamp
        self.event_type = eventType
        self.resource = resource

    def __str__(self):
        return "{event_id: %s, timestamp: %s, event_type: %s, resource: %s}" % (
            self.event_id,
            self.timestamp,
            self.event_type,
            self.resource,
        )
