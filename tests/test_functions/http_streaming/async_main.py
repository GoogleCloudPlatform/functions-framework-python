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

"""Async function used in Worker tests of handling HTTP functions."""

import asyncio

from starlette.responses import StreamingResponse


async def function(request):
    """Test async HTTP function that reads a stream of integers and returns a stream
    providing the sum of values read so far.

    Args:
      request: The HTTP request which triggered this function. Must contain a
      stream of new line separated integers.

    Returns:
      A Starlette StreamingResponse.
    """
    print("INVOKED THE ASYNC STREAM FUNCTION!!!")

    body = await request.body()
    body_str = body.decode("utf-8")
    lines = body_str.strip().split("\n") if body_str.strip() else []

    def generate():
        sum_so_far = 0
        for line in lines:
            if line.strip():
                sum_so_far += float(line)
                yield (str(sum_so_far) + "\n").encode("utf-8")

    return StreamingResponse(generate())
