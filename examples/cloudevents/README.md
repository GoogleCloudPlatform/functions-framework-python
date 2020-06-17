# Deploying a CloudEvent function to Cloud Run with the Functions Framework
This sample uses the [Cloud Events SDK](https://github.com/cloudevents/sdk-python) to send and receive a CloudEvent on Cloud Run.

## How to run this locally
Build the Docker image:

```commandline
docker build --tag ff_example .
```

Run the image and bind the correct ports.

```commandline
docker run -p:8080:8080 ff_example
```

Send an event to the container:

```python
from cloudevents.sdk import converters
from cloudevents.sdk import marshaller
from cloudevents.sdk.converters import structured
from cloudevents.sdk.event import v1
import requests
import json

def run_structured(event, url):
    http_marshaller = marshaller.NewDefaultHTTPMarshaller()
    structured_headers, structured_data = http_marshaller.ToRequest(
        event, converters.TypeStructured, json.dumps
    )
    print("structured CloudEvent")
    print(structured_data.getvalue())

    response = requests.post(url,
                             headers=structured_headers,
                             data=structured_data.getvalue())
    response.raise_for_status()

event = (
    v1.Event()
    .SetContentType("application/json")
    .SetData('{"name":"john"}')
    .SetEventID("my-id")
    .SetSource("from-galaxy-far-far-away")
    .SetEventTime("tomorrow")
    .SetEventType("cloudevent.greet.you")
)

run_structured(event, "http://0.0.0.0:8080/")

```
