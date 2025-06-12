import asyncio
import json

from cloudevents.http import to_json

import functions_framework.aio

filename = "function_output.json"


class RawJson:
    data: dict

    def __init__(self, data):
        self.data = data

    @staticmethod
    def from_dict(obj: dict) -> "RawJson":
        return RawJson(obj)

    def to_dict(self) -> dict:
        return self.data


def _write_output(content):
    with open(filename, "w") as f:
        f.write(content)


async def write_http(request):
    json_data = await request.json()
    _write_output(json.dumps(json_data))
    return "OK", 200


async def write_cloud_event(cloud_event):
    _write_output(to_json(cloud_event).decode())


@functions_framework.aio.http
async def write_http_declarative(request):
    json_data = await request.json()
    _write_output(json.dumps(json_data))
    return "OK", 200


@functions_framework.aio.cloud_event
async def write_cloud_event_declarative(cloud_event):
    _write_output(to_json(cloud_event).decode())


@functions_framework.aio.http
async def write_http_declarative_concurrent(request):
    await asyncio.sleep(1)
    return "OK", 200


# Note: Typed events are not supported in ASGI mode yet
# Legacy event functions are also not supported in ASGI mode