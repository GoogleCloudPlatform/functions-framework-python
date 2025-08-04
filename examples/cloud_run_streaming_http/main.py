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

import time
import asyncio
import functions_framework
import functions_framework.aio
from starlette.responses import StreamingResponse

# Helper function for the synchronous streaming example.
def slow_numbers(minimum, maximum):
    yield '<html><body><ul>'
    for number in range(minimum, maximum + 1):
        yield '<li>%d</li>' % number
        time.sleep(0.5)
    yield '</ul></body></html>'

@functions_framework.http
def hello_stream(request):
    """
    A synchronous HTTP function that streams a response.
    Args:
        request (flask.Request): The request object.
    Returns:
        A generator, which will be streamed as the response.
    """
    generator = slow_numbers(1, 10)
    return generator, {'Content-Type': 'text/html'}

# Helper function for the asynchronous streaming example.
async def slow_numbers_async(minimum, maximum):
    yield '<html><body><ul>'
    for number in range(minimum, maximum + 1):
        yield '<li>%d</li>' % number
        await asyncio.sleep(0.5)
    yield '</ul></body></html>'

@functions_framework.aio.http
async def hello_stream_async(request):
    """
    An asynchronous HTTP function that streams a response.
    Args:
        request (starlette.requests.Request): The request object.
    Returns:
        A starlette.responses.StreamingResponse.
    """
    generator = slow_numbers_async(1, 10)
    return StreamingResponse(generator, media_type='text/html')
