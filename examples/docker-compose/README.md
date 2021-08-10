# Developing functions with Docker Compose

## Introduction

This examples shows you how to develop a Cloud Function locally with Docker Compose, including live reloading.

## Install `docker-compose`:
https://docs.docker.com/compose/install/

## Start the `docker-compose` environment:

In this directory, bring up the `docker-compose` environment with:
```
docker-compose up
```

You should see output similar to:

```
Building function
[+] Building 7.0s (10/10) FINISHED
 => [internal] load build definition from Dockerfile                 0.0s
 => => transferring dockerfile: 431B                                 0.0s
 => [internal] load .dockerignore                                    0.0s
 => => transferring context: 2B                                      0.0s
 => [internal] load metadata for docker.io/library/python:latest     0.6s
 => [1/5] FROM docker.io/library/python@sha256:7a93befe45f3afb6b337  0.0s
 => [internal] load build context                                    0.0s
 => => transferring context: 2.11kB                                  0.0s
 => CACHED [2/5] WORKDIR /func                                       0.0s
 => [3/5] COPY . .                                                   0.0s
 => [4/5] RUN pip install functions-framework                        4.7s
 => [5/5] RUN pip install -r requirements.txt                        1.1s
 => exporting to image                                               0.4s
 => => exporting layers                                              0.4s
 => => writing image sha256:99962e5907e80856af6b032aa96a3130dde9ab6  0.0s
 => => naming to docker.io/library/docker-compose_function           0.0s

Use 'docker scan' to run Snyk tests against images to find vulnerabilities and learn how to fix them
Recreating docker-compose_function_1 ... done
Attaching to docker-compose_function_1
function_1  |  * Serving Flask app 'hello' (lazy loading)
function_1  |  * Environment: production
function_1  |    WARNING: This is a development server. Do not use it in a production deployment.
function_1  |    Use a production WSGI server instead.
function_1  |  * Debug mode: on
function_1  |  * Running on all addresses.
function_1  |    WARNING: This is a development server. Do not use it in a production deployment.
function_1  |  * Running on http://172.21.0.2:8080/ (Press CTRL+C to quit)
function_1  |  * Restarting with watchdog (inotify)
function_1  |  * Debugger is active!
```
function_1  |  * Debugger PIN: 162-882-413

## Call your Cloud Function

Leaving the previous command running, in a **new terminal**, call your functions. To call the `hello` function:

```bash
curl localhost:8080/hello
```

You should see output similar to:

```terminal
Hello, World!
```
