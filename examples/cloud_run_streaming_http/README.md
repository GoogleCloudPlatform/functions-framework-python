# Deploying streaming functions to Cloud Run

This sample shows how to deploy streaming functions to [Cloud Run](http://cloud.google.com/run) with the Functions Framework. The `main.py` file contains examples for both synchronous and asynchronous streaming.

## Dependencies
Install the dependencies for this example:
```sh
pip install -r requirements.txt
```

## Running locally

### Synchronous Streaming
To run the synchronous streaming function locally:
```sh
functions-framework --target=hello_stream
```
Then, send a request to it from another terminal:
```sh
curl localhost:8080
```

### Asynchronous Streaming
To run the asynchronous streaming function locally:
```sh
functions-framework --target=hello_stream_async
```
Then, send a request to it from another terminal:
```sh
curl localhost:8080
```

## Deploying to Cloud Run
You can deploy these functions to Cloud Run using the `gcloud` CLI.

### Synchronous Streaming
```sh
gcloud run deploy streaming-function \
    --source . \
    --function hello_stream \
    --base-image python312 \
    --region <YOUR_REGION>
```

### Asynchronous Streaming
```sh
gcloud run deploy streaming-async-function \
    --source . \
    --function hello_stream_async \
    --base-image python312 \
    --region <YOUR_REGION>
```

```