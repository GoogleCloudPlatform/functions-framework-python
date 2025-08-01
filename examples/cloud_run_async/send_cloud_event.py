#!/usr/local/bin/python

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
import asyncio
import httpx

from cloudevents.http import CloudEvent, to_structured

async def main():
    # Create a cloudevent
    attributes = {
        "Content-Type": "application/json",
        "source": "from-galaxy-far-far-away",
        "type": "cloudevent.greet.you",
    }
    data = {"name": "john"}

    event = CloudEvent(attributes, data)

    # Send the event to the local functions-framework server
    headers, data = to_structured(event)
    
    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:8080/", headers=headers, data=data)

if __name__ == "__main__":
    asyncio.run(main())