import json

filename = "function_output.json"


def _write_json(content):
    with open(filename, "w") as f:
        f.write(json.dumps(content))


def write_http(request):
    _write_json(request.json)
    return "OK", 200


def write_legacy_event(data, context):
    _write_json(
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


def write_cloud_event(cloudevent):
    cloudevent.datacontenttype = "application/json"
    _write_json(cloudevent)
