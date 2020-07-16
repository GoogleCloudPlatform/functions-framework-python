# Builds the conformance tester and runs it.
# To build this file, ensure you are in the root directory, i.e. one level up from here, and run
# $ docker build -t conformance -f conformance_tests/Dockerfile .
# then, to run it
# $ docker run -e source="tests/conformance_tests/cloud_event_test.py" -e signature="cloudevent" -e test_type="cloudevent" -t conformance
FROM golang:1.14.5 AS builder
WORKDIR /src
RUN apt-get update && apt-get install -y git
RUN go version

# TODO(joelgerard): Are we going to pull from main branch?
RUN git clone https://github.com/GoogleCloudPlatform/functions-framework-conformance.git
RUN cd /src/functions-framework-conformance/client && go build

FROM python:3.7-slim
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .
COPY --from=builder /src/functions-framework-conformance/client/client .

RUN pip install gunicorn
RUN pip install /app


CMD exec ./client -cmd "functions-framework --target=test --signature-type=$signature --source=$source" -type=$test_type
