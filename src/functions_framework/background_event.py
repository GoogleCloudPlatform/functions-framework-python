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


class BackgroundEvent(object):
    """BackgroundEvent is an event passed to GCF background event functions.

    Background event functions take data and context as parameters, both of
    which this class represents. By contrast, CloudEvent functions take a
    single CloudEvent object as their parameter. This class does not represent
    CloudEvents.
    """

    # Supports v1beta1, v1beta2, and v1 event formats.
    def __init__(
        self,
        context=None,
        data="",
        eventId="",
        timestamp="",
        eventType="",
        resource="",
        **kwargs,
    ):
        self.context = context
        if not self.context:
            self.context = {
                "eventId": eventId,
                "timestamp": timestamp,
                "eventType": eventType,
                "resource": resource,
            }
        self.data = data
