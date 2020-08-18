# Deploying a CloudEvent Function to Cloud Run with the Functions Framework

This sample uses the [CloudEvents SDK](https://github.com/cloudevents/sdk-python) to send and receive a [CloudEvent](http://cloudevents.io) on Cloud Run.

## How to run this locally

Build the Docker image:

```commandline
docker build -t cloudevent_example .
```

Run the image and bind the correct ports:

```commandline
docker run --rm -p 8080:8080 -e PORT=8080 ff_example
```

Send an event to the container:

```python
python send_cloudevent.py
```
