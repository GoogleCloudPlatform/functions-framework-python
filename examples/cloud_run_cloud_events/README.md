# Deploying a CloudEvent Function to Cloud Run with the Functions Framework

This sample uses the [CloudEvents SDK](https://github.com/cloudevents/sdk-python) to send and receive a [CloudEvent](http://cloudevents.io) on Cloud Run.

## How to run this locally

Build the Docker image:

```commandline
docker build -t cloud_event_example .
```

Run the image and bind the correct ports:

```commandline
docker run --rm -p 8080:8080 -e PORT=8080 cloud_event_example
```

Send an event to the container:

```python
docker run -t cloud_event_example send_cloud_event.py
```
