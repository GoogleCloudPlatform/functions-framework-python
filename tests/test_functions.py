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

import os
import pathlib
import re
import time

import pretend
import pytest

import functions_framework

from functions_framework import LazyWSGIApp, create_app, exceptions

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"

# Python 3.5: ModuleNotFoundError does not exist
try:
    _ModuleNotFoundError = ModuleNotFoundError
except:
    _ModuleNotFoundError = ImportError


@pytest.fixture
def background_json(tmpdir):
    return {
        "context": {
            "eventId": "some-eventId",
            "timestamp": "some-timestamp",
            "eventType": "some-eventType",
            "resource": "some-resource",
        },
        "data": {"filename": str(tmpdir / "filename.txt"), "value": "some-value"},
    }


def test_http_function_executes_success():
    source = TEST_FUNCTIONS_DIR / "http_trigger" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.post("/my_path", json={"mode": "SUCCESS"})
    assert resp.status_code == 200
    assert resp.data == b"success"


def test_http_function_executes_failure():
    source = TEST_FUNCTIONS_DIR / "http_trigger" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.get("/", json={"mode": "FAILURE"})
    assert resp.status_code == 400
    assert resp.data == b"failure"


def test_http_function_executes_throw():
    source = TEST_FUNCTIONS_DIR / "http_trigger" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.put("/", json={"mode": "THROW"})
    assert resp.status_code == 500


def test_http_function_request_url_empty_path():
    source = TEST_FUNCTIONS_DIR / "http_request_check" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.get("", json={"mode": "url"})
    assert resp.status_code == 308
    assert resp.location == "http://localhost/"


def test_http_function_request_url_slash():
    source = TEST_FUNCTIONS_DIR / "http_request_check" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.get("/", json={"mode": "url"})
    assert resp.status_code == 200
    assert resp.data == b"http://localhost/"


def test_http_function_rquest_url_path():
    source = TEST_FUNCTIONS_DIR / "http_request_check" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.get("/my_path", json={"mode": "url"})
    assert resp.status_code == 200
    assert resp.data == b"http://localhost/my_path"


def test_http_function_request_path_slash():
    source = TEST_FUNCTIONS_DIR / "http_request_check" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.get("/", json={"mode": "path"})
    assert resp.status_code == 200
    assert resp.data == b"/"


def test_http_function_request_path_path():
    source = TEST_FUNCTIONS_DIR / "http_request_check" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.get("/my_path", json={"mode": "path"})
    assert resp.status_code == 200
    assert resp.data == b"/my_path"


def test_http_function_check_env_function_target():
    source = TEST_FUNCTIONS_DIR / "http_check_env" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.post("/", json={"mode": "FUNCTION_TARGET"})
    assert resp.status_code == 200
    assert resp.data == b"function"


def test_http_function_check_env_function_signature_type():
    source = TEST_FUNCTIONS_DIR / "http_check_env" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.post("/", json={"mode": "FUNCTION_SIGNATURE_TYPE"})
    assert resp.status_code == 200
    assert resp.data == b"http"


def test_http_function_execution_time():
    source = TEST_FUNCTIONS_DIR / "http_trigger_sleep" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    start_time = time.time()
    resp = client.get("/", json={"mode": "1000"})
    execution_time_sec = time.time() - start_time

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_invalid_function_definition_missing_function_file():
    source = TEST_FUNCTIONS_DIR / "missing_function_file" / "main.py"
    target = "functions"

    with pytest.raises(exceptions.MissingSourceException) as excinfo:
        create_app(target, source)

    assert re.match(
        "File .* that is expected to define function doesn't exist", str(excinfo.value)
    )


def test_invalid_configuration():
    with pytest.raises(exceptions.InvalidConfigurationException) as excinfo:
        create_app(None, None, None)

    assert (
        "Target is not specified (FUNCTION_TARGET environment variable not set)"
        == str(excinfo.value)
    )


def test_invalid_signature_type():
    source = TEST_FUNCTIONS_DIR / "http_trigger" / "main.py"
    target = "function"

    with pytest.raises(exceptions.FunctionsFrameworkException) as excinfo:
        create_app(target, source, "invalid_signature_type")


def test_http_function_flask_render_template():
    source = TEST_FUNCTIONS_DIR / "http_flask_render_template" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.post("/", json={"message": "test_message"})

    assert resp.status_code == 200
    assert resp.data == (
        b"<!doctype html>\n<html>\n"
        b"   <body>\n"
        b"      <h1>Hello test_message!</h1>\n"
        b"   </body>\n"
        b"</html>"
    )


def test_http_function_with_import():
    source = TEST_FUNCTIONS_DIR / "http_with_import" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.data == b"Hello"


@pytest.mark.parametrize(
    "method, data",
    [
        ("get", b"GET"),
        ("head", b""),  # body will be empty
        ("post", b"POST"),
        ("put", b"PUT"),
        ("delete", b"DELETE"),
        ("options", b"OPTIONS"),
        ("trace", b"TRACE"),
        ("patch", b"PATCH"),
    ],
)
def test_http_function_all_methods(method, data):
    source = TEST_FUNCTIONS_DIR / "http_method_check" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = getattr(client, method)("/")

    assert resp.status_code == 200
    assert resp.data == data


@pytest.mark.parametrize("path", ["robots.txt", "favicon.ico"])
def test_error_paths(path):
    source = TEST_FUNCTIONS_DIR / "http_trigger" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.get("/{}".format(path))

    assert resp.status_code == 404
    assert b"Not Found" in resp.data


@pytest.mark.parametrize(
    "target, source, signature_type",
    [(None, None, None), (pretend.stub(), pretend.stub(), pretend.stub()),],
)
def test_lazy_wsgi_app(monkeypatch, target, source, signature_type):
    actual_app_stub = pretend.stub()
    wsgi_app = pretend.call_recorder(lambda *a, **kw: actual_app_stub)
    create_app = pretend.call_recorder(lambda *a: wsgi_app)
    monkeypatch.setattr(functions_framework, "create_app", create_app)

    # Test that it's lazy
    lazy_app = LazyWSGIApp(target, source, signature_type)

    assert lazy_app.app == None

    args = [pretend.stub(), pretend.stub()]
    kwargs = {"a": pretend.stub(), "b": pretend.stub()}

    # Test that it's initialized when called
    app = lazy_app(*args, **kwargs)

    assert app == actual_app_stub
    assert create_app.calls == [pretend.call(target, source, signature_type)]
    assert wsgi_app.calls == [pretend.call(*args, **kwargs)]

    # Test that it's only initialized once
    app = lazy_app(*args, **kwargs)

    assert app == actual_app_stub
    assert wsgi_app.calls == [
        pretend.call(*args, **kwargs),
        pretend.call(*args, **kwargs),
    ]


def test_class_in_main_is_in_right_module():
    source = TEST_FUNCTIONS_DIR / "module_is_correct" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()
    resp = client.get("/")

    assert resp.status_code == 200


def test_flask_current_app_is_available():
    source = TEST_FUNCTIONS_DIR / "flask_current_app" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()
    resp = client.get("/")

    assert resp.status_code == 200


def test_function_returns_none():
    source = TEST_FUNCTIONS_DIR / "returns_none" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()
    resp = client.get("/")

    assert resp.status_code == 500


def test_legacy_function_check_env(monkeypatch):
    source = TEST_FUNCTIONS_DIR / "http_check_env" / "main.py"
    target = "function"

    monkeypatch.setenv("ENTRY_POINT", target)

    client = create_app(target, source).test_client()
    resp = client.post("/", json={"mode": "FUNCTION_TRIGGER_TYPE"})
    assert resp.status_code == 200
    assert resp.data == b"http"

    resp = client.post("/", json={"mode": "FUNCTION_NAME"})
    assert resp.status_code == 200
    assert resp.data.decode("utf-8") == target


def test_legacy_function_returns_none(monkeypatch):
    source = TEST_FUNCTIONS_DIR / "returns_none" / "main.py"
    target = "function"

    monkeypatch.setenv("ENTRY_POINT", target)

    client = create_app(target, source).test_client()
    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.data == b"OK"
