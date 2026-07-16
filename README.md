# Functions Framework for Python

[![PyPI version](https://badge.fury.io/py/functions-framework.svg)](https://badge.fury.io/py/functions-framework)

[![Python unit CI][ff_python_unit_img]][ff_python_unit_link] [![Python lint CI][ff_python_lint_img]][ff_python_lint_link] [![Python conformance CI][ff_python_conformance_img]][ff_python_conformance_link] ![Security Scorecard](https://api.securityscorecards.dev/projects/github.com/GoogleCloudPlatform/functions-framework-python/badge)

An open source FaaS (Function as a service) framework for writing portable
Python functions -- brought to you by the Google Cloud Functions team.

The Functions Framework lets you write lightweight functions that run in many
different environments, including:

*   [Google Cloud Run Functions](https://cloud.google.com/functions/)
*   Your local development machine
*   [Knative](https://github.com/knative/)-based environments

The framework allows you to go from:

def hello(request):
    return "Hello world!"

To:

curl http://my-url
# Output: Hello world!

All without needing to worry about writing an HTTP server or complicated request handling logic.

## Features

*   Spin up a local development server for quick testing
*   Invoke a function in response to a request
*   Automatically unmarshal events conforming to the [CloudEvents](https://cloudevents.io/) spec
*   Portable between serverless platforms

## Installation

Install the Functions Framework via `pip`:

pip install functions-framework

Or, for deployment, add the Functions Framework to your `requirements.txt` file:

functions-framework==3.*

## Quickstarts

### Quickstart: HTTP Function (Hello World)

Create an `main.py` file with the following contents:

import flask
import functions_framework

@functions_framework.http
def hello(request: flask.Request) -> flask.typing.ResponseReturnValue:
    return "Hello world!"

> Your function is passed a single parameter, `(request)`, which is a Flask [`Request`](https://flask.palletsprojects.com/en/3.0.x/api/#flask.Request) object.

Run the following command:

functions-framework --target hello --debug
 * Serving Flask app "hello" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://0.0.0.0:8080/ (Press CTRL+C to quit)

(You can also use `functions-framework-python` if you have multiple
language frameworks installed).

Open http://localhost:8080/ in your browser and see *Hello world!*.

Or send requests to this function using `curl` from another terminal window:

curl localhost:8080
# Output: Hello world!

### Quickstart: CloudEvent Function

Create an `main.py` file with the following contents:

import functions_framework
from cloudevents.http.event import CloudEvent

@functions_framework.cloud_event
def hello_cloud_event(cloud_event: CloudEvent) -> None:
   print(f"Received event with ID: {cloud_event['id']} and data {cloud_event.data}")

> Your function is passed a single [CloudEvent](https://github.com/cloudevents/sdk-python/blob/main/cloudevents/sdk/event/v1.py) parameter.

Run the following command to run `hello_cloud_event` target locally:

functions-framework --target=hello_cloud_event

In a different terminal, `curl` the Functions Framework server:

curl -X POST localhost:8080 \
   -H "Content-Type: application/cloudevents+json" \
   -d '{
	"specversion" : "1.0",
	"type" : "example.com.cloud.event",
	"source" : "https://example.com/cloudevents/pull",
	"subject" : "123",
	"id" : "A234-1234-1234",
	"time" : "2018-04-05T17:31:00Z",
	"data" : "hello world"
}'

Output from the terminal running `functions-framework`:
Received event with ID: A234-1234-1234 and data hello world
 

More info on sending [CloudEvents](http://cloudevents.io) payloads, see [`examples/cloud_run_cloud_events`](examples/cloud_run_cloud_events/) instruction.


### Quickstart: Error handling

The framework includes an error handler that is similar to the
[`flask.Flask.errorhandler`](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.errorhandler)
function, which allows you to handle specific error types with a decorator:

import functions_framework


@functions_framework.errorhandler(ZeroDivisionError)
def handle_zero_division(e):
    return "I'm a teapot", 418


def function(request):
    1 / 0
    return "Success", 200

This function will catch the `ZeroDivisionError` and return a different
response instead.

### Quickstart: Pub/Sub emulator
1. Create a `main.py` file with the following contents:

      def hello(event, context):
        print("Received", context.event_id)
   
1. Start the Functions Framework on port 8080:

      functions-framework --target=hello --signature-type=event --debug --port=8080
   
1. In a second terminal, start the Pub/Sub emulator on port 8085.

      export PUBSUB_PROJECT_ID=my-project
   gcloud beta emulators pubsub start \
       --project=$PUBSUB_PROJECT_ID \
       --host-port=localhost:8085
   
   You should see the following after the Pub/Sub emulator has started successfully:

      [pubsub] INFO: Server started, listening on 8085
   
1. In a third terminal, create a Pub/Sub topic and attach a push subscription to the topic, using `http://localhost:8080` as its push endpoint. [Publish](https://cloud.google.com/pubsub/docs/quickstart-client-libraries#publish_messages) some messages to the topic. Observe your function getting triggered by the Pub/Sub messages.

      export PUBSUB_PROJECT_ID=my-project
   export TOPIC_ID=my-topic
   export PUSH_SUBSCRIPTION_ID=my-subscription
   $(gcloud beta emulators pubsub env-init)

   git clone https://github.com/googleapis/python-pubsub.git
   cd python-pubsub/samples/snippets/
   pip install -r requirements.txt

   python publisher.py $PUBSUB_PROJECT_ID create $TOPIC_ID
   python subscriber.py $PUBSUB_PROJECT_ID create-push $TOPIC_ID $PUSH_SUBSCRIPTION_ID http://localhost:8080
   python publisher.py $PUBSUB_PROJECT_ID publish $TOPIC_ID
   
   You should see the following after the commands have run successfully:

      Created topic: projects/my-project/topics/my-topic

   topic: "projects/my-project/topics/my-topic"
   push_config {
     push_endpoint: "http://localhost:8080"
   }
   ack_deadline_seconds: 10
   message_retention_duration {
     seconds: 604800
   }
   .
   Endpoint for subscription is: http://localhost:8080

   1
   2
   3
   4
   5
   6
   7
   8
   9
   Published messages to projects/my-project/topics/my-topic.
   
   And in the terminal where the Functions Framework is running:

       * Serving Flask app "hello" (lazy loading)
    * Environment: production
      WARNING: This is a development server. Do not use it in a production deployment.
      Use a production WSGI server instead.
    * Debug mode: on
    * Running on http://0.0.0.0:8080/ (Press CTRL+C to quit)
    * Restarting with fsevents reloader
    * Debugger is active!
    * Debugger PIN: 911-794-046
   Received 1
   127.0.0.1 - - [11/Aug/2021 14:42:22] "POST / HTTP/1.1" 200 -
   Received 2
   127.0.0.1 - - [11/Aug/2021 14:42:22] "POST / HTTP/1.1" 200 -
   Received 5
   127.0.0.1 - - [11/Aug/2021 14:42:22] "POST / HTTP/1.1" 200 -
   Received 6
   127.0.0.1 - - [11/Aug/2021 14:42:22] "POST / HTTP/1.1" 200 -
   Received 7
   127.0.0.1 - - [11/Aug/2021 14:42:22] "POST / HTTP/1.1" 200 -
   Received 8
   127.0.0.1 - - [11/Aug/2021 14:42:22] "POST / HTTP/1.1" 200 -
   Received 9
   127.0.0.1 - - [11/Aug/2021 14:42:39] "POST / HTTP/1.1" 200 -
   Received 3
   127.0.0.1 - - [11/Aug/2021 14:42:39] "POST / HTTP/1.1" 200 -
   Received 4
   127.0.0.1 - - [11/Aug/2021 14:42:39] "POST / HTTP/1.1" 200 -
   
For more details on extracting data from a Pub/Sub event, see
https://cloud.google.com/pubsub/docs/push
