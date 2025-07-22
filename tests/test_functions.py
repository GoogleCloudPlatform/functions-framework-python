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
import time

import pretend
import pytest

if sys.version_info >= (3, 8):
    from starlette.testclient import TestClient as StarletteTestClient
else:
    StarletteTestClient = None

import functions_framework

from functions_framework import LazyWSGIApp, create_app, errorhandler, exceptions

if sys.version_info >= (3, 8):
    from functions_framework.aio import create_asgi_app
else:
    create_asgi_app = None

TEST_FUNCTIONS_DIR = pathlib.Path.cwd() / "tests" / "test_functions"


# Python 3.5: ModuleNotFoundError does not exist
try:
    _ModuleNotFoundError = ModuleNotFoundError
except:
    _ModuleNotFoundError = ImportError


@pytest.fixture
def tempfile_payload(tmpdir):
    return {"filename": str(tmpdir / "filename.txt"), "value": "some-value"}


@pytest.fixture
def background_json(tempfile_payload):
    return {
        "context": {
            "eventId": "some-eventId",
            "timestamp": "some-timestamp",
            "eventType": "some-eventType",
            "resource": "some-resource",
        },
        "data": tempfile_payload,
    }


@pytest.fixture
def background_event_client():
    source = TEST_FUNCTIONS_DIR / "background_trigger" / "main.py"
    target = "function"
    return create_app(target, source, "event").test_client()


@pytest.fixture
def create_ce_headers():
    return lambda event_type: {
        "ce-id": "my-id",
        "ce-source": "//firebasedatabase.googleapis.com/projects/_/instances/my-project-id",
        "ce-type": event_type,
        "ce-specversion": "1.0",
        "ce-subject": "refs/gcf-test/xyz",
        "ce-time": "2020-08-16T13:58:54.471765",
    }


@pytest.fixture(params=["main.py", "async_main.py"])
def http_trigger_client(request):
    source = TEST_FUNCTIONS_DIR / "http_trigger" / request.param
    target = "function"
    if not request.param.startswith("async_"):
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app, raise_server_exceptions=False)


@pytest.fixture(params=["main.py", "async_main.py"])
def http_request_check_client(request):
    source = TEST_FUNCTIONS_DIR / "http_request_check" / request.param
    target = "function"
    if not request.param.startswith("async_"):
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(
        app,
        # Override baseurl to use localhost instead of default http://testserver.
        base_url="http://localhost",
    )


@pytest.fixture(params=["main.py", "async_main.py"])
def http_check_env_client(request):
    source = TEST_FUNCTIONS_DIR / "http_check_env" / request.param
    target = "function"
    if not request.param.startswith("async_"):
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app)


@pytest.fixture(params=["main.py", "async_main.py"])
def http_trigger_sleep_client(request):
    source = TEST_FUNCTIONS_DIR / "http_trigger_sleep" / request.param
    target = "function"
    if not request.param.startswith("async_"):
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app)


@pytest.fixture(params=["main.py", "async_main.py"])
def http_with_import_client(request):
    source = TEST_FUNCTIONS_DIR / "http_with_import" / request.param
    target = "function"
    if not request.param.startswith("async_"):
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app)


@pytest.fixture(params=["sync", "async"])
def http_method_check_client(request):
    source = TEST_FUNCTIONS_DIR / "http_method_check" / "main.py"
    target = "function"
    if not request.param == "async":
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app)


@pytest.fixture(params=["sync", "async"])
def module_is_correct_client(request):
    source = TEST_FUNCTIONS_DIR / "module_is_correct" / "main.py"
    target = "function"
    if not request.param == "async":
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app)


@pytest.fixture(params=["sync", "async"])
def returns_none_client(request):
    source = TEST_FUNCTIONS_DIR / "returns_none" / "main.py"
    target = "function"
    if not request.param == "async":
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app)


@pytest.fixture(params=["sync", "async"])
def relative_imports_client(request):
    source = TEST_FUNCTIONS_DIR / "relative_imports" / "main.py"
    target = "function"
    if not request.param == "async":
        return create_app(target, source).test_client()
    app = create_asgi_app(target, source)
    return StarletteTestClient(app)


def test_http_function_executes_success(http_trigger_client):
    resp = http_trigger_client.post("/my_path", json={"mode": "SUCCESS"})
    assert resp.status_code == 200
    assert resp.text == "success"


def test_http_function_executes_failure(http_trigger_client):
    resp = http_trigger_client.post("/", json={"mode": "FAILURE"})
    assert resp.status_code == 400
    assert resp.text == "failure"


def test_http_function_executes_throw(http_trigger_client):
    resp = http_trigger_client.put("/", json={"mode": "THROW"})
    assert resp.status_code == 500


def test_http_function_request_url_empty_path(http_request_check_client):
    # Starlette TestClient normalizes empty path "" to "/" before making the request,
    # while Flask preserves the empty path and lets the server handle the redirect
    if StarletteTestClient and isinstance(
        http_request_check_client, StarletteTestClient
    ):
        # Starlette TestClient converts "" to "/" so we get a direct 200 response
        resp = http_request_check_client.post("", json={"mode": "url"})
        assert resp.status_code == 200
        assert resp.text == "http://localhost/"
    else:
        # Flask returns a 308 redirect from empty path to "/"
        resp = http_request_check_client.post("", json={"mode": "url"})
        assert resp.status_code == 308
        assert resp.location == "http://localhost/"


def test_http_function_request_url_slash(http_request_check_client):
    resp = http_request_check_client.post("/", json={"mode": "url"})
    assert resp.status_code == 200
    assert resp.text == "http://localhost/"


def test_http_function_rquest_url_path(http_request_check_client):
    resp = http_request_check_client.post("/my_path", json={"mode": "url"})
    assert resp.status_code == 200
    assert resp.text == "http://localhost/my_path"


def test_http_function_request_path_slash(http_request_check_client):
    resp = http_request_check_client.post("/", json={"mode": "path"})
    assert resp.status_code == 200
    assert resp.text == "/"


def test_http_function_request_path_path(http_request_check_client):
    resp = http_request_check_client.post("/my_path", json={"mode": "path"})
    assert resp.status_code == 200
    assert resp.text == "/my_path"


def test_http_function_check_env_function_target(http_check_env_client):
    resp = http_check_env_client.post("/", json={"mode": "FUNCTION_TARGET"})
    assert resp.status_code == 200
    # Use .content for StarletteTestClient, .data for Flask test client (both return bytes)
    data = getattr(resp, "content", getattr(resp, "data", None))
    assert data == b"function"


def test_http_function_check_env_function_signature_type(http_check_env_client):
    resp = http_check_env_client.post("/", json={"mode": "FUNCTION_SIGNATURE_TYPE"})
    assert resp.status_code == 200
    assert resp.text == "http"


def test_http_function_execution_time(http_trigger_sleep_client):
    start_time = time.time()
    resp = http_trigger_sleep_client.post("/", json={"mode": "1000"})
    execution_time_sec = time.time() - start_time

    assert resp.status_code == 200
    assert resp.text == "OK"
    # Check that the execution time is roughly correct (allowing some buffer)
    assert execution_time_sec > 0.9


def test_background_function_executes(background_event_client, background_json):
    resp = background_event_client.post("/", json=background_json)
    assert resp.status_code == 200


def test_background_function_supports_get(background_event_client, background_json):
    resp = background_event_client.get("/")
    assert resp.status_code == 200


def test_background_function_executes_entry_point_one(background_json):
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "myFunctionFoo"

    client = create_app(target, source, "event").test_client()

    resp = client.post("/", json=background_json)
    assert resp.status_code == 200


def test_background_function_executes_entry_point_two(background_json):
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "myFunctionBar"

    client = create_app(target, source, "event").test_client()

    resp = client.post("/", json=background_json)
    assert resp.status_code == 200


def test_multiple_calls(background_json):
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "myFunctionFoo"

    client = create_app(target, source, "event").test_client()

    resp = client.post("/", json=background_json)
    assert resp.status_code == 200
    resp = client.post("/", json=background_json)
    assert resp.status_code == 200
    resp = client.post("/", json=background_json)
    assert resp.status_code == 200


def test_pubsub_payload(background_event_client, background_json):
    resp = background_event_client.post("/", json=background_json)
    assert resp.status_code == 200
    assert resp.data == b"OK"

    with open(background_json["data"]["filename"]) as f:
        assert f.read() == '{{"entryPoint": "function", "value": "{}"}}'.format(
            background_json["data"]["value"]
        )


def test_background_function_no_data(background_event_client, background_json):
    headers = {"Content-Type": "application/json"}
    resp = background_event_client.post("/", headers=headers)
    assert resp.status_code == 400


def test_invalid_function_definition_missing_function_file():
    source = TEST_FUNCTIONS_DIR / "missing_function_file" / "main.py"
    target = "functions"

    with pytest.raises(exceptions.MissingSourceException) as excinfo:
        create_app(target, source)

    assert re.match(
        "File .* that is expected to define function doesn't exist", str(excinfo.value)
    )


@pytest.mark.parametrize("create_app", [create_app, create_asgi_app])
def test_invalid_function_definition_multiple_entry_points(create_app):
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "function"

    with pytest.raises(exceptions.MissingTargetException) as excinfo:
        create_app(target, source, "event")

    assert re.match(
        "File .* is expected to contain a function named 'function'. Found: 'fun', 'myFunctionBar', 'myFunctionFoo' instead",
        str(excinfo.value),
    )


@pytest.mark.parametrize("create_app", [create_app, create_asgi_app])
def test_invalid_function_definition_multiple_entry_points_invalid_function(create_app):
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "invalidFunction"

    with pytest.raises(exceptions.MissingTargetException) as excinfo:
        create_app(target, source, "event")

    assert re.match(
        "File .* is expected to contain a function named 'invalidFunction'. Found: 'fun', 'myFunctionBar', 'myFunctionFoo' instead",
        str(excinfo.value),
    )


@pytest.mark.parametrize("create_app", [create_app, create_asgi_app])
def test_invalid_function_definition_multiple_entry_points_not_a_function(create_app):
    source = TEST_FUNCTIONS_DIR / "background_multiple_entry_points" / "main.py"
    target = "notAFunction"

    with pytest.raises(exceptions.InvalidTargetTypeException) as excinfo:
        create_app(target, source, "event")

    assert re.match(
        "The function defined in file .* as 'notAFunction' needs to be of type "
        "function. Got: .*",
        str(excinfo.value),
    )


@pytest.mark.parametrize("create_app", [create_app, create_asgi_app])
def test_invalid_function_definition_function_syntax_error(create_app):
    source = TEST_FUNCTIONS_DIR / "background_load_error" / "main.py"
    target = "function"

    with pytest.raises(SyntaxError) as excinfo:
        create_app(target, source, "event")

    assert any(
        (
            "invalid syntax" in str(excinfo.value),  # Python <3.8
            "unmatched ')'" in str(excinfo.value),  # Python >3.8
        )
    )


def test_invalid_function_definition_function_syntax_robustness_with_debug(monkeypatch):
    monkeypatch.setattr(
        functions_framework.werkzeug.serving, "is_running_from_reloader", lambda: True
    )
    source = TEST_FUNCTIONS_DIR / "background_load_error" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()

    resp = client.get("/")
    assert resp.status_code == 500


@pytest.mark.parametrize("create_app", [create_app, create_asgi_app])
def test_invalid_function_definition_missing_dependency(create_app):
    source = TEST_FUNCTIONS_DIR / "background_missing_dependency" / "main.py"
    target = "function"

    with pytest.raises(_ModuleNotFoundError) as excinfo:
        create_app(target, source, "event")

    assert "No module named 'nonexistentpackage'" in str(excinfo.value)


@pytest.mark.parametrize("create_app", [create_app, create_asgi_app])
def test_invalid_configuration(create_app):
    with pytest.raises(exceptions.InvalidConfigurationException) as excinfo:
        create_app(None, None, None)

    assert (
        "Target is not specified (FUNCTION_TARGET environment variable not set)"
        == str(excinfo.value)
    )


@pytest.mark.parametrize("create_app", [create_app, create_asgi_app])
def test_invalid_signature_type(create_app):
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


def test_http_function_with_import(http_with_import_client):
    resp = http_with_import_client.get("/")

    assert resp.status_code == 200
    assert resp.text == "Hello"


@pytest.mark.parametrize(
    "method, text",
    [
        ("get", "GET"),
        ("head", ""),  # body will be empty
        ("post", "POST"),
        ("put", "PUT"),
        ("delete", "DELETE"),
        ("options", "OPTIONS"),
        # ("trace", "TRACE"), # unsupported in httpx
        ("patch", "PATCH"),
    ],
)
def test_http_function_all_methods(http_method_check_client, method, text):
    resp = getattr(http_method_check_client, method)("/")

    assert resp.status_code == 200
    assert resp.text == text


@pytest.mark.parametrize("path", ["robots.txt", "favicon.ico"])
def test_error_paths(http_trigger_client, path):
    resp = http_trigger_client.get("/{}".format(path))

    assert resp.status_code == 404
    assert "Not Found" in resp.text


@pytest.mark.parametrize(
    "target, source, signature_type",
    [(None, None, None), (pretend.stub(), pretend.stub(), pretend.stub())],
)
def test_lazy_wsgi_app(monkeypatch, target, source, signature_type):
    actual_app_stub = pretend.stub()
    wsgi_app = pretend.call_recorder(lambda *a, **kw: actual_app_stub)
    create_app = pretend.call_recorder(lambda *a, **kw: wsgi_app)
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


def test_dummy_error_handler():
    @errorhandler("foo", bar="baz")
    def function():
        pass


def test_class_in_main_is_in_right_module(module_is_correct_client):
    resp = module_is_correct_client.get("/")

    assert resp.status_code == 200


def test_flask_current_app_is_available():
    source = TEST_FUNCTIONS_DIR / "flask_current_app" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()
    resp = client.get("/")

    assert resp.status_code == 200


def test_function_returns_none(returns_none_client):
    resp = returns_none_client.get("/")

    assert resp.status_code == 500


def test_function_returns_stream():
    source = TEST_FUNCTIONS_DIR / "http_streaming" / "main.py"
    target = "function"

    client = create_app(target, source).test_client()
    resp = client.post("/", data="1\n2\n3\n4\n")

    assert resp.status_code == 200
    assert resp.is_streamed
    assert resp.data.decode("utf-8") == "1.0\n3.0\n6.0\n10.0\n"


def test_async_function_returns_stream():
    source = TEST_FUNCTIONS_DIR / "http_streaming" / "async_main.py"
    target = "function"

    client = StarletteTestClient(create_asgi_app(target, source))

    collected_response = ""
    with client.stream("POST", "/", content="1\n2\n3\n4\n") as resp:
        assert resp.status_code == 200
        for text in resp.iter_text():
            collected_response += text
    assert collected_response == "1.0\n3.0\n6.0\n10.0\n"


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


@pytest.mark.parametrize(
    "mode, expected",
    [
        ("loginfo", '"severity": "INFO"'),
        ("logwarn", '"severity": "ERROR"'),
        ("logerr", '"severity": "ERROR"'),
        ("logcrit", '"severity": "ERROR"'),
        ("stdout", '"severity": "INFO"'),
        ("stderr", '"severity": "ERROR"'),
    ],
)
def test_legacy_function_log_severity(monkeypatch, capfd, mode, expected):
    source = TEST_FUNCTIONS_DIR / "http_check_severity" / "main.py"
    target = "function"

    monkeypatch.setenv("ENTRY_POINT", target)

    client = create_app(target, source).test_client()
    resp = client.post("/", json={"mode": mode})
    captured = capfd.readouterr().err
    assert resp.status_code == 200
    assert expected in captured


def test_legacy_function_log_exception(monkeypatch, capfd):
    source = TEST_FUNCTIONS_DIR / "http_log_exception" / "main.py"
    target = "function"
    severity = '"severity": "ERROR"'
    traceback = "Traceback (most recent call last)"

    monkeypatch.setenv("ENTRY_POINT", target)

    client = create_app(target, source).test_client()
    resp = client.post("/")
    captured = capfd.readouterr().err
    assert resp.status_code == 200
    assert severity in captured
    assert traceback in captured


def test_legacy_function_returns_none(monkeypatch):
    source = TEST_FUNCTIONS_DIR / "returns_none" / "main.py"
    target = "function"

    monkeypatch.setenv("ENTRY_POINT", target)

    client = create_app(target, source).test_client()
    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_errorhandler(monkeypatch):
    source = TEST_FUNCTIONS_DIR / "errorhandler" / "main.py"
    target = "function"

    monkeypatch.setenv("ENTRY_POINT", target)

    client = create_app(target, source).test_client()
    resp = client.get("/")

    assert resp.status_code == 418
    assert resp.data == b"I'm a teapot"


@pytest.mark.parametrize(
    "event_type",
    [
        "google.cloud.firestore.document.v1.written",
        "google.cloud.pubsub.topic.v1.messagePublished",
        "google.cloud.storage.object.v1.finalized",
        "google.cloud.storage.object.v1.metadataUpdated",
        "google.firebase.analytics.log.v1.written",
        "google.firebase.auth.user.v1.created",
        "google.firebase.auth.user.v1.deleted",
        "google.firebase.database.ref.v1.written",
    ],
)
def tests_cloud_to_background_event_client(
    background_event_client, create_ce_headers, tempfile_payload, event_type
):
    headers = create_ce_headers(event_type)
    resp = background_event_client.post("/", headers=headers, json=tempfile_payload)

    assert resp.status_code == 200
    with open(tempfile_payload["filename"]) as json_file:
        data = json.load(json_file)
        assert data["value"] == "some-value"


def tests_cloud_to_background_event_client_invalid_source(
    background_event_client, create_ce_headers, tempfile_payload
):
    headers = create_ce_headers("google.cloud.firestore.document.v1.written")
    headers["ce-source"] = "invalid"

    resp = background_event_client.post("/", headers=headers, json=tempfile_payload)

    assert resp.status_code == 500


def test_relative_imports(relative_imports_client):
    resp = relative_imports_client.get("/")
    assert resp.status_code == 200
    assert resp.text == "success"
