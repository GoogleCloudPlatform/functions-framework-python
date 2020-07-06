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

import pretend

import functions_framework


def test_http_view_func_wrapper():
    function = pretend.call_recorder(lambda request: "Hello")
    request_object = pretend.stub()
    local_proxy = pretend.stub(_get_current_object=lambda: request_object)

    view_func = functions_framework._http_view_func_wrapper(function, local_proxy)
    view_func("/some/path")

    assert function.calls == [pretend.call(request_object)]


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
