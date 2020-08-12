# Deploying a CloudEvent function to Cloud Run with the Functions Framework

This sample uses the [Cloud Events SDK](https://github.com/cloudevents/sdk-python) to send and receive a CloudEvent on Cloud Run.

## How to run this locally

Build the Docker image:

```commandline
docker build -t ff_example .
```

Run the image and bind the correct ports:

```commandline
docker run --rm -p 8080:8080 -e PORT=8080 ff_example
```

Send an event to the container:

```python
from cloudevents.http import CloudEvent, to_structured_http
import requests
import json

# Create event
attributes = {
    "Content-Type": "application/json",
    "source": "from-galaxy-far-far-away",
    "type": "cloudevent.greet.you"
}
data = {"name":"john"}

event = CloudEvent(attributes, data)
print(event)

# Send event
headers, data = to_structured_http(event)
response = requests.post("http://localhost:8080/", headers=headers, data=data)
response.raise_for_status()
```
