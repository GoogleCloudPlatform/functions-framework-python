import json

from cloudevents.http import to_json

filename = "function_output.json"


def _write_output(content):
    with open(filename, "w") as f:
        f.write(content)


def write_http(request):
    _write_output(json.dumps(request.json))
    return "OK", 200


def write_legacy_event(data, context):
    _write_output(
        json.dumps(
            {
                "data": data,
                "context": {
                    "eventId": context.event_id,
                    "timestamp": context.timestamp,
                    "eventType": context.event_type,
                    "resource": context.resource,
                },
            }
        )
    )


def write_cloud_event(cloudevent):
    _write_output(to_json(cloudevent).decode())
