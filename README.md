# Functions Framework for Python [![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2FGoogleCloudPlatform%2Ffunctions-framework-python%2Fbadge&style=flat)](https://actions-badge.atrox.dev/GoogleCloudPlatform/functions-framework-python/goto) [![PyPI version](https://badge.fury.io/py/functions-framework.svg)](https://badge.fury.io/py/functions-framework)

An open source FaaS (Function as a service) framework for writing portable
Python functions -- brought to you by the Google Cloud Functions team.

The Functions Framework lets you write lightweight functions that run in many
different environments, including:

*   [Google Cloud Functions](https://cloud.google.com/functions/)
*   Your local development machine
*   [Cloud Run and Cloud Run for Anthos](https://cloud.google.com/run/)
*   [Knative](https://github.com/knative/)-based environments

The framework allows you to go from:

```python
def hello(request):
    return "Hello world!"
```

To:

```sh
curl http://my-url
# Output: Hello world!
```

All without needing to worry about writing an HTTP server or complicated request handling logic.

## Features

*   Spin up a local development server for quick testing
*   Invoke a function in response to a request
*   Automatically unmarshal events conforming to the [CloudEvents](https://cloudevents.io/) spec
*   Portable between serverless platforms

## Installation

Install the Functions Framework via `pip`:

```sh
pip install functions-framework
```

Or, for deployment, add the Functions Framework to your `requirements.txt` file:

```
functions-framework==2.0.0
```

## Quickstarts

### Quickstart: Hello, World on your local machine

Create an `main.py` file with the following contents:

```python
def hello(request):
    return "Hello world!"
```

Run the following command:

```sh
functions-framework --target=hello
```

Open http://localhost:8080/ in your browser and see *Hello world!*.


### Quickstart: Set up a new project

Create a `main.py` file with the following contents:

```python
def hello(request):
    return "Hello world!"
```

Now install the Functions Framework:

```sh
pip install functions-framework
```

Use the `functions-framework` command to start the built-in local development server:

```sh
functions-framework --target hello --debug
 * Serving Flask app "hello" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:8080/ (Press CTRL+C to quit)
```

(You can also use `functions-framework-python` if you potentially have multiple
language frameworks installed).

Send requests to this function using `curl` from another terminal window:

```sh
curl localhost:8080
# Output: Hello world!
```

### Quickstart: Build a Deployable Container

1. Install [Docker](https://store.docker.com/search?type=edition&offering=community) and the [`pack` tool](https://buildpacks.io/docs/install-pack/).

1. Build a container from your function using the Functions [buildpacks](https://github.com/GoogleCloudPlatform/buildpacks):
	```sh
	pack build \
		--builder gcr.io/buildpacks/builder:v1 \
		--env GOOGLE_FUNCTION_SIGNATURE_TYPE=http \
		--env GOOGLE_FUNCTION_TARGET=hello \
		my-first-function
	```

1. Start the built container:
	```sh
	docker run --rm -p 8080:8080 my-first-function
	# Output: Serving function...
	```

1. Send requests to this function using `curl` from another terminal window:
	```sh
	curl localhost:8080
	# Output: Hello World!
	```

## Run your function on serverless platforms

### Google Cloud Functions

This Functions Framework is based on the [Python Runtime on Google Cloud Functions](https://cloud.google.com/functions/docs/concepts/python-runtime).

On Cloud Functions, using the Functions Framework is not necessary: you don't need to add it to your `requirements.txt` file.

After you've written your function, you can simply deploy it from your local machine using the `gcloud` command-line tool. [Check out the Cloud Functions quickstart](https://cloud.google.com/functions/docs/quickstart).

### Cloud Run/Cloud Run on GKE

Once you've written your function and added the Functions Framework to your `requirements.txt` file, all that's left is to create a container image. [Check out the Cloud Run quickstart](https://cloud.google.com/run/docs/quickstarts/build-and-deploy) for Python to create a container image and deploy it to Cloud Run. You'll write a `Dockerfile` when you build your container. This `Dockerfile` allows you to specify exactly what goes into your container (including custom binaries, a specific operating system, and more). [Here is an example `Dockerfile` that calls Functions Framework.](https://github.com/GoogleCloudPlatform/functions-framework-python/blob/master/examples/cloud_run_http)

If you want even more control over the environment, you can [deploy your container image to Cloud Run on GKE](https://cloud.google.com/run/docs/quickstarts/prebuilt-deploy-gke). With Cloud Run on GKE, you can run your function on a GKE cluster, which gives you additional control over the environment (including use of GPU-based instances, longer timeouts and more).

### Container environments based on Knative

Cloud Run and Cloud Run on GKE both implement the [Knative Serving API](https://www.knative.dev/docs/). The Functions Framework is designed to be compatible with Knative environments. Just build and deploy your container to a Knative environment.

## Configure the Functions Framework

You can configure the Functions Framework using command-line flags or environment variables. If you specify both, the environment variable will be ignored.

| Command-line flag  | Environment variable      | Description                                                                                                                                                                                      |
| ------------------ | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--host`           | `HOST`                    | The host on which the Functions Framework listens for requests. Default: `0.0.0.0`                                                                                                               |
| `--port`           | `PORT`                    | The port on which the Functions Framework listens for requests. Default: `8080`                                                                                                                  |
| `--target`         | `FUNCTION_TARGET`         | The name of the exported function to be invoked in response to requests. Default: `function`                                                                                                     |
| `--signature-type` | `FUNCTION_SIGNATURE_TYPE` | The signature used when writing your function. Controls unmarshalling rules and determines which arguments are used to invoke your function. Default: `http`; accepted values: `http` or `event` or `cloudevent` |
| `--source`         | `FUNCTION_SOURCE`         | The path to the file containing your function. Default: `main.py` (in the current working directory)                                                                                             |
| `--debug`          | `DEBUG`                   | A flag that allows to run functions-framework to run in debug mode, including live reloading. Default: `False`                                                                                   |


## Enable Google Cloud Functions Events

The Functions Framework can unmarshall incoming
Google Cloud Functions [event](https://cloud.google.com/functions/docs/concepts/events-triggers#events) payloads to `data` and `context` objects.
These will be passed as arguments to your function when it receives a request.
Note that your function must use the `event`-style function signature:


```python
def hello(data, context):
    print(data)
    print(context)
```

To enable automatic unmarshalling, set the function signature type to `event`
using a command-line flag or an environment variable. By default, the HTTP
signature will be used and automatic event unmarshalling will be disabled.

For more details on this signature type, check out the Google Cloud Functions
documentation on
[background functions](https://cloud.google.com/functions/docs/writing/background#cloud_pubsub_example).

See the [running example](examples/cloud_run_event).

## Enable CloudEvents

The Functions Framework can unmarshall incoming
[CloudEvent](http://cloudevents.io) payloads to a `cloudevent` object.
It will be passed as an argument to your function when it receives a request.
Note that your function must use the `cloudevent`-style function signature


```python
def hello(cloudevent):
    print("Received event with ID: %s" % cloudevent.EventID())
    return 200
```

To enable automatic unmarshalling, set the function signature type to `cloudevent` using the `--signature-type` command-line flag or the `FUNCTION_SIGNATURE_TYPE` environment variable. By default, the HTTP signature type will be used and automatic event unmarshalling will be disabled.

See the [running example](examples/cloud_run_cloudevents).

## Advanced Examples

More advanced guides can be found in the [`examples/`](https://github.com/GoogleCloudPlatform/functions-framework-python/blob/master/examples/) directory.
You can also find examples on using the CloudEvent Python SDK [here](https://github.com/cloudevents/sdk-python).

## Contributing

Contributions to this library are welcome and encouraged. See [CONTRIBUTING](CONTRIBUTING.md) for more information on how to get started.
