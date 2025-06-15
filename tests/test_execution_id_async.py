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
import json
import pathlib

from unittest.mock import Mock

import pytest

from starlette.testclient import TestClient

from functions_framework import execution_id
from functions_framework.aio import create_asgi_app

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"
TEST_EXECUTION_ID = "test_execution_id"
TEST_SPAN_ID = "123456"


def test_async_user_function_can_retrieve_execution_id_from_header():
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


def test_async_uncaught_exception_in_user_function_sets_execution_id(
    capsys, monkeypatch
):
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


def test_async_print_from_user_function_sets_execution_id(capsys, monkeypatch):
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


def test_async_log_from_user_function_sets_execution_id(capsys, monkeypatch):
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


def test_async_user_function_can_retrieve_generated_execution_id(monkeypatch):
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


def test_async_does_not_set_execution_id_when_not_enabled(capsys):
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


def test_async_concurrent_requests_maintain_separate_execution_ids(capsys, monkeypatch):
    monkeypatch.setenv("LOG_EXECUTION_ID", "true")

    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "async_sleep"
    app = create_asgi_app(target, source)
    # Use separate clients to avoid connection pooling issues
    client1 = TestClient(app, raise_server_exceptions=False)
    client2 = TestClient(app, raise_server_exceptions=False)

    # Make concurrent requests with explicit execution IDs
    import threading

    def make_request(client, message, exec_id):
        client.post(
            "/",
            headers={
                "Content-Type": "application/json",
                "Function-Execution-Id": exec_id,
            },
            json={"message": message},
        )

    thread1 = threading.Thread(
        target=lambda: make_request(client1, "message1", "exec-id-1")
    )
    thread2 = threading.Thread(
        target=lambda: make_request(client2, "message2", "exec-id-2")
    )

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    record = capsys.readouterr()
    logs = record.err.strip().split("\n")
    logs_as_json = [json.loads(log) for log in logs if log]

    # Check that each message appears twice (once at start, once at end of async_sleep)
    # and that each has the correct execution ID
    message1_logs = [log for log in logs_as_json if log.get("message") == "message1"]
    message2_logs = [log for log in logs_as_json if log.get("message") == "message2"]

    assert (
        len(message1_logs) == 2
    ), f"Expected 2 logs for message1, got {len(message1_logs)}"
    assert (
        len(message2_logs) == 2
    ), f"Expected 2 logs for message2, got {len(message2_logs)}"

    # Check that all message1 logs have exec-id-1
    for log in message1_logs:
        assert log["logging.googleapis.com/labels"]["execution_id"] == "exec-id-1"

    # Check that all message2 logs have exec-id-2
    for log in message2_logs:
        assert log["logging.googleapis.com/labels"]["execution_id"] == "exec-id-2"


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
def test_async_set_execution_context_headers(
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
async def test_crash_handler_without_context_sets_execution_id():
    """Test that crash handler returns proper error response with crash header."""
    from functions_framework.aio import _crash_handler

    # Create a mock request
    request = Mock()
    request.url.path = "/test"
    request.method = "POST"
    request.headers = {"Function-Execution-Id": "test-exec-id"}

    # Create an exception
    exc = ValueError("Test error")

    # Call crash handler
    response = await _crash_handler(request, exc)

    # Check response
    assert response.status_code == 500
    assert response.headers["X-Google-Status"] == "crash"


def test_async_decorator_with_sync_function():
    """Test that the async decorator handles sync functions properly."""
    from functions_framework.execution_id import set_execution_context_async

    # Create a sync function
    def sync_func(request):
        return {"status": "ok"}

    # Apply the async decorator
    wrapped = set_execution_context_async(enable_id_logging=False)(sync_func)

    # Create mock request
    request = Mock()
    request.headers = Mock()
    request.headers.get = Mock(return_value="")

    # Call the wrapped function - it should be sync since the original was sync
    result = wrapped(request)

    assert result == {"status": "ok"}


def test_sync_function_called_from_async_context():
    """Test that a sync function works correctly when called from async ASGI app."""
    source = TEST_FUNCTIONS_DIR / "execution_id" / "async_main.py"
    target = "sync_function_in_async_context"
    app = create_asgi_app(target, source)
    client = TestClient(app)
    resp = client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
    )

    result = resp.json()
    assert result["execution_id"] == TEST_EXECUTION_ID
    assert result["type"] == "sync"
