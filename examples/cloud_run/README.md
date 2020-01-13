# Deploy a function to Cloud Run

[![Run on Google Cloud](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)

This guide will show you how to deploy the following example function to [Cloud Run](https://cloud.google.com/run):

```python
def hello(request):
    return "Hello world!"
```

This guide assumes your Python function is defined in a `main.py` file and dependencies are specified in `requirements.txt` file.

## Running your function in a container

To run your function in a container, create a `Dockerfile` with the following contents:

```Dockerfile
# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.7-slim

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .

# Install production dependencies.
RUN pip install gunicorn functions-framework
RUN pip install -r requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 -e FUNCTION_TARGET=hello functions_framework:app
```

Start the container locally by running `docker build` and `docker run`:

```sh
docker build -t helloworld . && docker run --rm -p 8080:8080 -e PORT=8080 helloworld
```

Send requests to this function using `curl` from another terminal window:

```sh
curl localhost:8080
# Output: Hello world!
```

## Configure gcloud

To use Docker with gcloud, [configure the Docker credential helper](https://cloud.google.com/container-registry/docs/advanced-authentication):

```sh
gcloud auth configure-docker
```

## Deploy a Container

You can deploy your containerized function to Cloud Run by following the [Cloud Run quickstart](https://cloud.google.com/run/docs/quickstarts/build-and-deploy).

Use the `docker` and `gcloud` CLIs to build and deploy a container to Cloud Run, replacing `[PROJECT-ID]` with the project id and `helloworld` with a different image name if necessary:

```sh
docker build -t gcr.io/[PROJECT-ID]/helloworld .
docker push gcr.io/[PROJECT-ID]/helloworld
gcloud run deploy helloworld --image gcr.io/[PROJECT-ID]/helloworld --region us-central1
```

If you want even more control over the environment, you can [deploy your container image to Cloud Run on GKE](https://cloud.google.com/run/docs/quickstarts/prebuilt-deploy-gke). With Cloud Run on GKE, you can run your function on a GKE cluster, which gives you additional control over the environment (including use of GPU-based instances, longer timeouts and more).
