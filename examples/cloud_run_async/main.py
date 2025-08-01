# Copyright 2025 Google LLC
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

import functions_framework.aio

@functions_framework.aio.http
async def hello_async_http(request):
    """
    An async HTTP function.
    Args:
        request (starlette.requests.Request): The request object.
    Returns:
        The response text, or an instance of any Starlette response class
        (e.g. `starlette.responses.Response`).
    """
    return "Hello, async world!"

@functions_framework.aio.cloud_event
async def hello_async_cloudevent(cloud_event):
    """
    An async CloudEvent function.
    Args:
        cloud_event (cloudevents.http.CloudEvent): The CloudEvent object.
    """
    print(f"Received event with ID: {cloud_event['id']} and data {cloud_event.data}")
