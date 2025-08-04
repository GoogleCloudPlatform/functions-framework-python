# Deploying async functions to Cloud Run

This sample shows how to deploy asynchronous functions to [Cloud Run functions](https://cloud.google.com/functions) with the Functions Framework. It includes examples for both HTTP and CloudEvent functions, which can be found in the `main.py` file.

## Dependencies

Install the dependencies for this example:

```sh
pip install -r requirements.txt
```

## Running locally

### HTTP Function

To run the HTTP function locally, use the `functions-framework` command:

```sh
functions-framework --target=hello_async_http
```

Then, send a request to it from another terminal:

```sh
curl localhost:8080
# Output: Hello, async world!
```

### CloudEvent Function

To run the CloudEvent function, specify the target and set the signature type:

```sh
functions-framework --target=hello_async_cloudevent --signature-type=cloudevent
```

Then, in another terminal, send a sample CloudEvent using the provided script:

```sh
python send_cloud_event.py
```

## Deploying to Cloud Run

You can deploy these functions to Cloud Run using the `gcloud` CLI.

### HTTP Function

```sh
gcloud run deploy async-http-function \
    --source . \
    --function hello_async_http \
    --base-image python312 \
    --region <YOUR_REGION>
```

### CloudEvent Function

```sh
gcloud run deploy async-cloudevent-function \
    --source . \
    --function hello_async_cloudevent \
    --base-image python312 \
    --region <YOUR_REGION>
```

After deploying, you can invoke the CloudEvent function by sending an HTTP POST request with a CloudEvent payload to its URL.
