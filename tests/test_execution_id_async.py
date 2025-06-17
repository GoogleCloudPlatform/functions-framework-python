# Copyright 2025 Google LLC
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
import asyncio
import json
import pathlib
import re

from functools import partial
from unittest.mock import Mock

import pytest

from starlette.testclient import TestClient

from functions_framework import execution_id
from functions_framework.aio import create_asgi_app

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"
TEST_EXECUTION_ID = "test_execution_id"
TEST_SPAN_ID = "123456"


def test_user_function_can_retrieve_execution_id_from_header():
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_function"
    app = create_asgi_app(target, source)
    client = TestClient(app)
    resp = client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
    )

    assert resp.json()["execution_id"] == TEST_EXECUTION_ID


def test_uncaught_exception_in_user_function_sets_execution_id(capsys, monkeypatch):
    monkeypatch.setenv("LOG_EXECUTION_ID", "true")
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_error"
    app = create_asgi_app(target, source)
    # Don't raise server exceptions so we can capture the logs
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 500
    record = capsys.readouterr()
    assert f'"execution_id": "{TEST_EXECUTION_ID}"' in record.err
    assert '"logging.googleapis.com/labels"' in record.err
    assert "ZeroDivisionError" in record.err


def test_print_from_user_function_sets_execution_id(capsys, monkeypatch):
    monkeypatch.setenv("LOG_EXECUTION_ID", "true")
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_print_message"
    app = create_asgi_app(target, source)
    client = TestClient(app)
    client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
        json={"message": "some-message"},
    )
    record = capsys.readouterr()
    assert f'"execution_id": "{TEST_EXECUTION_ID}"' in record.out
    assert '"message": "some-message"' in record.out


def test_log_from_user_function_sets_execution_id(capsys, monkeypatch):
    monkeypatch.setenv("LOG_EXECUTION_ID", "true")
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_log_message"
    app = create_asgi_app(target, source)
    client = TestClient(app)
    client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
        json={"message": json.dumps({"custom-field": "some-message"})},
    )
    record = capsys.readouterr()
    assert f'"execution_id": "{TEST_EXECUTION_ID}"' in record.err
    assert '"custom-field": "some-message"' in record.err
    assert '"logging.googleapis.com/labels"' in record.err


def test_user_function_can_retrieve_generated_execution_id(monkeypatch):
    monkeypatch.setattr(
        execution_id, "_generate_execution_id", lambda: TEST_EXECUTION_ID
    )
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_function"
    app = create_asgi_app(target, source)
    client = TestClient(app)
    resp = client.post(
        "/",
        headers={
            "Content-Type": "application/json",
        },
    )

    assert resp.json()["execution_id"] == TEST_EXECUTION_ID


def test_does_not_set_execution_id_when_not_enabled(capsys):
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_print_message"
    app = create_asgi_app(target, source)
    client = TestClient(app)
    client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
        json={"message": "some-message"},
    )
    record = capsys.readouterr()
    assert f'"execution_id": "{TEST_EXECUTION_ID}"' not in record.out
    assert "some-message" in record.out


def test_does_not_set_execution_id_when_env_var_is_false(capsys, monkeypatch):
    monkeypatch.setenv("LOG_EXECUTION_ID", "false")
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_print_message"
    app = create_asgi_app(target, source)
    client = TestClient(app)
    client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
        json={"message": "some-message"},
    )
    record = capsys.readouterr()
    assert f'"execution_id": "{TEST_EXECUTION_ID}"' not in record.out
    assert "some-message" in record.out


def test_does_not_set_execution_id_when_env_var_is_not_bool_like(capsys, monkeypatch):
    monkeypatch.setenv("LOG_EXECUTION_ID", "maybe")
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_print_message"
    app = create_asgi_app(target, source)
    client = TestClient(app)
    client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
        json={"message": "some-message"},
    )
    record = capsys.readouterr()
    assert f'"execution_id": "{TEST_EXECUTION_ID}"' not in record.out
    assert "some-message" in record.out


def test_generate_execution_id():
    expected_matching_regex = "^[0-9a-zA-Z]{12}$"
    actual_execution_id = execution_id._generate_execution_id()

    match = re.match(expected_matching_regex, actual_execution_id).group(0)
    assert match == actual_execution_id


@pytest.mark.parametrize(
    "headers,expected_execution_id,expected_span_id,should_generate",
    [
        (
            {
                "X-Cloud-Trace-Context": f"TRACE_ID/{TEST_SPAN_ID};o=1",
                "Function-Execution-Id": TEST_EXECUTION_ID,
            },
            TEST_EXECUTION_ID,
            TEST_SPAN_ID,
            False,
        ),
        ({}, None, None, True),  # Middleware will generate an ID
        (
            {
                "X-Cloud-Trace-Context": "malformed trace context string",
                "Function-Execution-Id": TEST_EXECUTION_ID,
            },
            TEST_EXECUTION_ID,
            None,
            False,
        ),
    ],
)
def test_set_execution_context_headers(
    headers, expected_execution_id, expected_span_id, should_generate
):
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_trace_test"
    app = create_asgi_app(target, source)
    client = TestClient(app)

    resp = client.post("/", headers=headers)

    result = resp.json()
    if should_generate:
        # When no execution ID is provided, middleware generates one
        assert result.get("execution_id") is not None
        assert len(result.get("execution_id")) == 12  # Generated IDs are 12 chars
    else:
        assert result.get("execution_id") == expected_execution_id
    assert result.get("span_id") == expected_span_id


@pytest.mark.asyncio
async def test_maintains_execution_id_for_concurrent_requests(monkeypatch, capsys):
    monkeypatch.setenv("LOG_EXECUTION_ID", "true")

    expected_logs = (
        {
            "message": "message1",
            "logging.googleapis.com/labels": {"execution_id": "test-execution-id-1"},
        },
        {
            "message": "message2",
            "logging.googleapis.com/labels": {"execution_id": "test-execution-id-2"},
        },
        {
            "message": "message1",
            "logging.googleapis.com/labels": {"execution_id": "test-execution-id-1"},
        },
        {
            "message": "message2",
            "logging.googleapis.com/labels": {"execution_id": "test-execution-id-2"},
        },
    )

    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_sleep"
    app = create_asgi_app(target, source)
    client = TestClient(app)
    loop = asyncio.get_event_loop()
    response1 = loop.run_in_executor(
        None,
        partial(
            client.post,
            "/",
            headers={
                "Content-Type": "application/json",
                "Function-Execution-Id": "test-execution-id-1",
            },
            json={"message": "message1"},
        ),
    )
    response2 = loop.run_in_executor(
        None,
        partial(
            client.post,
            "/",
            headers={
                "Content-Type": "application/json",
                "Function-Execution-Id": "test-execution-id-2",
            },
            json={"message": "message2"},
        ),
    )
    await asyncio.wait((response1, response2))
    record = capsys.readouterr()
    logs = record.err.strip().split("\n")
    logs_as_json = tuple(json.loads(log) for log in logs)

    sort_key = lambda d: d["message"]
    assert sorted(logs_as_json, key=sort_key) == sorted(expected_logs, key=sort_key)


def test_async_decorator_with_sync_function():
    def sync_func(request):
        return {"status": "ok"}

    wrapped = execution_id.set_execution_context_async(enable_id_logging=False)(
        sync_func
    )

    request = Mock()
    request.headers = Mock()
    request.headers.get = Mock(return_value="")

    result = wrapped(request)

    assert result == {"status": "ok"}


def test_sync_cloudevent_function_has_execution_context(monkeypatch, capsys):
    """Test that sync CloudEvent functions can access execution context."""
    monkeypatch.setenv("LOG_EXECUTION_ID", "true")

    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "sync_cloudevent_with_context"
    app = create_asgi_app(target, source, signature_type="cloudevent")
    client = TestClient(app)

    response = client.post(
        "/",
        headers={
            "ce-specversion": "1.0",
            "ce-type": "com.example.test",
            "ce-source": "test-source",
            "ce-id": "test-id",
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
        json={"message": "test"},
    )

    assert response.status_code == 200
    assert response.text == "OK"

    record = capsys.readouterr()
    assert f"Execution ID in sync CloudEvent: {TEST_EXECUTION_ID}" in record.err
    assert "No execution context in sync CloudEvent function!" not in record.err


def test_cloudevent_returns_500(capsys, monkeypatch):
    monkeypatch.setenv("LOG_EXECUTION_ID", "true")
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_cloudevent_error"
    app = create_asgi_app(target, source, signature_type="cloudevent")
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/",
        headers={
            "ce-specversion": "1.0",
            "ce-type": "com.example.test",
            "ce-source": "test-source",
            "ce-id": "test-id",
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 500
    record = capsys.readouterr()
    assert f'"execution_id": "{TEST_EXECUTION_ID}"' in record.err
    assert '"logging.googleapis.com/labels"' in record.err
    assert "ValueError" in record.err
