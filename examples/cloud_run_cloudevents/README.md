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
python send_cloudevent.py
```
