## How to run this locally

This guide shows how to run `hello_http` target locally.
To test with `hello_cloud_event`, change the target accordingly in Dockerfile.

Build the Docker image:

```commandline
docker build -t decorator_example .
```

Run the image and bind the correct ports:

```commandline
docker run --rm -p 8080:8080 -e PORT=8080 decorator_example
```

Send requests to this function using `curl` from another terminal window:

```sh
curl localhost:8080
# Output: Hello world!
```