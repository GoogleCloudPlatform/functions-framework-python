# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json

import pretend
import pytest
import werkzeug

from cloudevents.http import from_http

import functions_framework


def test_http_view_func_wrapper():
    function = pretend.call_recorder(lambda request: "Hello")
    request_object = pretend.stub()
    local_proxy = pretend.stub(_get_current_object=lambda: request_object, headers={})

    view_func = functions_framework._http_view_func_wrapper(function, local_proxy)
    view_func("/some/path")

    assert function.calls == [pretend.call(request_object)]


def test_http_view_func_wrapper_attribute_copied():
    def function(_):
        pass

    function.attribute = "foo"
    view_func = functions_framework._http_view_func_wrapper(function, pretend.stub())

    assert view_func.__name__ == "function"
    assert view_func.attribute == "foo"


def test_event_view_func_wrapper(monkeypatch):
    data = pretend.stub()
    json = {
        "context": {
            "eventId": "some-eventId",
            "timestamp": "some-timestamp",
            "eventType": "some-eventType",
            "resource": "some-resource",
        },
        "data": data,
    }
    request = pretend.stub(headers={}, get_json=lambda: json)

    context_stub = pretend.stub()
    context_class = pretend.call_recorder(lambda *a, **kw: context_stub)
    monkeypatch.setattr(functions_framework, "Context", context_class)
    function = pretend.call_recorder(lambda data, context: "Hello")

    view_func = functions_framework._event_view_func_wrapper(function, request)
    view_func("/some/path")

    assert function.calls == [pretend.call(data, context_stub)]
    assert context_class.calls == [
        pretend.call(
            eventId="some-eventId",
            timestamp="some-timestamp",
            eventType="some-eventType",
            resource="some-resource",
        )
    ]


def test_event_view_func_wrapper_bad_request(monkeypatch):
    request = pretend.stub(headers={}, get_json=lambda: None)

    context_stub = pretend.stub()
    context_class = pretend.call_recorder(lambda *a, **kw: context_stub)
    monkeypatch.setattr(functions_framework, "Context", context_class)
    function = pretend.call_recorder(lambda data, context: "Hello")

    view_func = functions_framework._event_view_func_wrapper(function, request)

    with pytest.raises(werkzeug.exceptions.BadRequest):
        view_func("/some/path")


def test_run_cloud_event():
    headers = {"Content-Type": "application/cloudevents+json"}
    data = json.dumps(
        {
            "source": "from-galaxy-far-far-away",
            "type": "cloud_event.greet.you",
            "specversion": "1.0",
            "id": "f6a65fcd-eed2-429d-9f71-ec0663d83025",
            "time": "2020-08-13T02:12:14.946587+00:00",
            "data": {"name": "john"},
        }
    )
    request = pretend.stub(headers=headers, get_data=lambda: data)

    function = pretend.call_recorder(lambda cloud_event: "hello")
    functions_framework._run_cloud_event(function, request)
    expected_cloud_event = from_http(request.headers, request.get_data())

    assert function.calls == [pretend.call(expected_cloud_event)]


def test_cloud_event_view_func_wrapper():
    headers = {"Content-Type": "application/cloudevents+json"}
    data = json.dumps(
        {
            "source": "from-galaxy-far-far-away",
            "type": "cloud_event.greet.you",
            "specversion": "1.0",
            "id": "f6a65fcd-eed2-429d-9f71-ec0663d83025",
            "time": "2020-08-13T02:12:14.946587+00:00",
            "data": {"name": "john"},
        }
    )

    request = pretend.stub(headers=headers, get_data=lambda: data)
    event = from_http(request.headers, request.get_data())

    function = pretend.call_recorder(lambda cloud_event: cloud_event)

    view_func = functions_framework._cloud_event_view_func_wrapper(function, request)
    view_func("/some/path")

    assert function.calls == [pretend.call(event)]


def test_binary_cloud_event_view_func_wrapper():
    headers = {
        "ce-specversion": "1.0",
        "ce-source": "from-galaxy-far-far-away",
        "ce-type": "cloud_event.greet.you",
        "ce-id": "f6a65fcd-eed2-429d-9f71-ec0663d83025",
        "ce-time": "2020-08-13T02:12:14.946587+00:00",
    }
    data = json.dumps({"name": "john"})

    request = pretend.stub(headers=headers, get_data=lambda: data)
    event = from_http(request.headers, request.get_data())

    function = pretend.call_recorder(lambda cloud_event: cloud_event)

    view_func = functions_framework._cloud_event_view_func_wrapper(function, request)
    view_func("/some/path")

    assert function.calls == [pretend.call(event)]


def test_binary_event_view_func_wrapper(monkeypatch):
    data = pretend.stub()
    request = pretend.stub(
        headers={
            "ce-type": "something",
            "ce-specversion": "something",
            "ce-source": "something",
            "ce-id": "something",
            "ce-eventId": "some-eventId",
            "ce-timestamp": "some-timestamp",
            "ce-eventType": "some-eventType",
            "ce-resource": "some-resource",
        },
        get_data=lambda: data,
    )

    context_stub = pretend.stub()
    context_class = pretend.call_recorder(lambda *a, **kw: context_stub)
    monkeypatch.setattr(functions_framework, "Context", context_class)
    function = pretend.call_recorder(lambda data, context: "Hello")

    view_func = functions_framework._event_view_func_wrapper(function, request)
    view_func("/some/path")

    assert function.calls == [pretend.call(data, context_stub)]
    assert context_class.calls == [
        pretend.call(
            eventId="some-eventId",
            timestamp="some-timestamp",
            eventType="some-eventType",
            resource="some-resource",
        )
    ]


def test_legacy_event_view_func_wrapper(monkeypatch):
    data = pretend.stub()
    json = {
        "eventId": "some-eventId",
        "timestamp": "some-timestamp",
        "eventType": "some-eventType",
        "resource": "some-resource",
        "data": data,
    }
    request = pretend.stub(headers={}, get_json=lambda: json)

    context_stub = pretend.stub()
    context_class = pretend.call_recorder(lambda *a, **kw: context_stub)
    monkeypatch.setattr(functions_framework, "Context", context_class)
    function = pretend.call_recorder(lambda data, context: "Hello")

    view_func = functions_framework._event_view_func_wrapper(function, request)
    view_func("/some/path")

    assert function.calls == [pretend.call(data, context_stub)]
    assert context_class.calls == [
        pretend.call(
            eventId="some-eventId",
            timestamp="some-timestamp",
            eventType="some-eventType",
            resource="some-resource",
        )
    ]
