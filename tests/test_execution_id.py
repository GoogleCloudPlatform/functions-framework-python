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
import pathlib
import re
import sys
from unittest.mock import Mock

import pretend
import pytest

from functions_framework import create_app, execution_id

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"
TEST_EXECUTION_ID = "test_execution_id"
TEST_SPAN_ID = "123456"


def test_user_function_can_retrieve_execution_id_from_header():
    source = TEST_FUNCTIONS_DIR / "execution_id" / "main.py"
    target = "function"
    client = create_app(target, source).test_client()
    resp = client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
        json={"delay": 1},
    )

    assert resp.get_json()["execution_id"] == TEST_EXECUTION_ID


def test_uncaught_exception_in_user_function_sets_execution_id(capsys, monkeypatch):
    monkeypatch.setenv("LOG_EXECUTION_ID", "True")
    source = TEST_FUNCTIONS_DIR / "execution_id" / "main.py"
    target = "error"
    app = create_app(target, source)
    client = app.test_client()
    resp = client.post(
        "/",
        headers={
            "Function-Execution-Id": TEST_EXECUTION_ID,
            "Content-Type": "application/json",
        },
        json={"delay": "not-a-valid-int-and-will-raise-an-exception"},
    )
    assert resp.status_code == 500
    record = capsys.readouterr()
    assert f'"execution_id": "{TEST_EXECUTION_ID}"' in record.err


def test_print_from_user_function_sets_execution_id(capsys, monkeypatch):
    monkeypatch.setenv("LOG_EXECUTION_ID", "True")
    source = TEST_FUNCTIONS_DIR / "execution_id" / "main.py"
    target = "print_message"
    app = create_app(target, source)
    client = app.test_client()
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
    monkeypatch.setenv("LOG_EXECUTION_ID", "True")
    source = TEST_FUNCTIONS_DIR / "execution_id" / "main.py"
    target = "log_message"
    app = create_app(target, source)
    client = app.test_client()
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


def test_user_function_can_retrieve_generated_execution_id(monkeypatch):
    monkeypatch.setattr(
        execution_id, "_generate_execution_id", lambda: TEST_EXECUTION_ID
    )
    source = TEST_FUNCTIONS_DIR / "execution_id" / "main.py"
    target = "function"
    client = create_app(target, source).test_client()
    resp = client.post(
        "/",
        headers={
            "Content-Type": "application/json",
        },
    )

    assert resp.get_json()["execution_id"] == TEST_EXECUTION_ID


def test_does_not_set_execution_id_when_not_enabled(capsys):
    source = TEST_FUNCTIONS_DIR / "execution_id" / "main.py"
    target = "print_message"
    app = create_app(target, source)
    client = app.test_client()
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
    "headers,expected_execution_id,expected_span_id",
    [
        (
            {
                "X-Cloud-Trace-Context": f"TRACE_ID/{TEST_SPAN_ID};o=1",
                "Function-Execution-Id": TEST_EXECUTION_ID,
            },
            TEST_EXECUTION_ID,
            TEST_SPAN_ID,
        ),
        (
            {
                "X-Cloud-Trace-Context": f"TRACE_ID/{TEST_SPAN_ID};o=1",
                "Function-Execution-Id": TEST_EXECUTION_ID,
            },
            TEST_EXECUTION_ID,
            TEST_SPAN_ID,
        ),
        ({}, None, None),
        (
            {
                "X-Cloud-Trace-Context": "malformed trace context string",
                "Function-Execution-Id": TEST_EXECUTION_ID,
            },
            TEST_EXECUTION_ID,
            None,
        ),
    ],
)
def test_set_execution_context(
    headers, expected_execution_id, expected_span_id, monkeypatch
):
    request = pretend.stub(headers=headers)

    def view_func():
        pass

    monkeypatch.setattr(
        execution_id, "_generate_execution_id", lambda: TEST_EXECUTION_ID
    )
    mock_g = Mock()
    monkeypatch.setattr(execution_id.flask, "g", mock_g)
    monkeypatch.setattr(execution_id.flask, "has_request_context", lambda: True)
    execution_id.set_execution_context(request)(view_func)()

    assert mock_g.execution_id_context.span_id == expected_span_id
    assert mock_g.execution_id_context.execution_id == expected_execution_id


@pytest.mark.parametrize(
    "log_message,expected_log_json",
    [
        ("text message", {"message": "text message"}),
        (
            json.dumps({"custom-field1": "value1", "custom-field2": "value2"}),
            {"custom-field1": "value1", "custom-field2": "value2"},
        ),
        ("[]", {"message": "[]"}),
    ],
)
def test_log_handler(monkeypatch, log_message, expected_log_json, capsys):
    log_handler = execution_id.LoggingHandlerAddExecutionId(stream=sys.stdout)
    monkeypatch.setattr(
        execution_id,
        "_get_current_context",
        lambda: execution_id.ExecutionContext(
            span_id=TEST_SPAN_ID, execution_id=TEST_EXECUTION_ID
        ),
    )
    expected_log_json.update(
        {
            "logging.googleapis.com/labels": {
                "execution_id": TEST_EXECUTION_ID,
            },
            "logging.googleapis.com/spanId": TEST_SPAN_ID,
        }
    )

    log_handler.write(log_message)
    record = capsys.readouterr()
    assert json.loads(record.out) == expected_log_json


def test_log_handler_omits_empty_execution_context(monkeypatch, capsys):
    log_handler = execution_id.LoggingHandlerAddExecutionId(stream=sys.stdout)
    monkeypatch.setattr(
        execution_id,
        "_get_current_context",
        lambda: execution_id.ExecutionContext(span_id=None, execution_id=None),
    )
    expected_json = {
        "message": "some message",
    }

    log_handler.write("some message")
    record = capsys.readouterr()
    assert json.loads(record.out) == expected_json
