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

import sys

import pretend
import pytest

from click.testing import CliRunner

import functions_framework
import functions_framework._function_registry as _function_registry
import functions_framework.aio

from functions_framework._cli import _cli


def test_cli_no_arguments():
    runner = CliRunner()
    result = runner.invoke(_cli)

    assert result.exit_code == 2
    assert "Missing option '--target'" in result.output


@pytest.mark.parametrize(
    "args, env, create_app_calls, run_calls",
    [
        (
            ["--target", "foo"],
            {},
            [pretend.call("foo", None, "http")],
            [pretend.call("0.0.0.0", 8080)],
        ),
        (
            [],
            {"FUNCTION_TARGET": "foo"},
            [pretend.call("foo", None, "http")],
            [pretend.call("0.0.0.0", 8080)],
        ),
        (
            ["--target", "foo", "--source", "/path/to/source.py"],
            {},
            [pretend.call("foo", "/path/to/source.py", "http")],
            [pretend.call("0.0.0.0", 8080)],
        ),
        (
            [],
            {"FUNCTION_TARGET": "foo", "FUNCTION_SOURCE": "/path/to/source.py"},
            [pretend.call("foo", "/path/to/source.py", "http")],
            [pretend.call("0.0.0.0", 8080)],
        ),
        (
            ["--target", "foo", "--signature-type", "event"],
            {},
            [pretend.call("foo", None, "event")],
            [pretend.call("0.0.0.0", 8080)],
        ),
        (
            [],
            {"FUNCTION_TARGET": "foo", "FUNCTION_SIGNATURE_TYPE": "event"},
            [pretend.call("foo", None, "event")],
            [pretend.call("0.0.0.0", 8080)],
        ),
        (
            ["--target", "foo", "--host", "127.0.0.1"],
            {},
            [pretend.call("foo", None, "http")],
            [pretend.call("127.0.0.1", 8080)],
        ),
        (
            ["--target", "foo", "--debug"],
            {},
            [pretend.call("foo", None, "http")],
            [pretend.call("0.0.0.0", 8080)],
        ),
        (
            [],
            {"FUNCTION_TARGET": "foo", "DEBUG": "True"},
            [pretend.call("foo", None, "http")],
            [pretend.call("0.0.0.0", 8080)],
        ),
    ],
)
def test_cli(monkeypatch, args, env, create_app_calls, run_calls):
    wsgi_server = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    wsgi_app = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    create_app = pretend.call_recorder(lambda *a, **kw: wsgi_app)
    monkeypatch.setattr(functions_framework._cli, "create_app", create_app)
    create_server = pretend.call_recorder(lambda *a, **kw: wsgi_server)
    monkeypatch.setattr(functions_framework._cli, "create_server", create_server)

    runner = CliRunner(env=env)
    result = runner.invoke(_cli, args)

    assert result.exit_code == 0
    assert create_app.calls == create_app_calls
    assert wsgi_server.run.calls == run_calls


def test_asgi_cli(monkeypatch):
    asgi_server = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    asgi_app = pretend.stub()

    create_asgi_app = pretend.call_recorder(lambda *a, **kw: asgi_app)
    aio_module = pretend.stub(create_asgi_app=create_asgi_app)
    monkeypatch.setitem(sys.modules, "functions_framework.aio", aio_module)

    create_server = pretend.call_recorder(lambda *a, **kw: asgi_server)
    monkeypatch.setattr(functions_framework._cli, "create_server", create_server)

    runner = CliRunner()
    result = runner.invoke(_cli, ["--target", "foo", "--asgi"])

    assert result.exit_code == 0
    assert create_asgi_app.calls == [pretend.call("foo", None, "http")]
    assert asgi_server.run.calls == [pretend.call("0.0.0.0", 8080)]


def test_auto_asgi_for_aio_decorated_functions(monkeypatch):
    original_asgi_functions = _function_registry.ASGI_FUNCTIONS.copy()
    _function_registry.ASGI_FUNCTIONS.clear()
    _function_registry.ASGI_FUNCTIONS.add("my_aio_func")

    asgi_app = pretend.stub()
    create_asgi_app = pretend.call_recorder(lambda *a, **k: asgi_app)
    aio_module = pretend.stub(create_asgi_app=create_asgi_app)
    monkeypatch.setitem(sys.modules, "functions_framework.aio", aio_module)

    asgi_server = pretend.stub(run=pretend.call_recorder(lambda host, port: None))
    create_server = pretend.call_recorder(lambda app, debug: asgi_server)
    monkeypatch.setattr(functions_framework._cli, "create_server", create_server)

    runner = CliRunner()
    result = runner.invoke(_cli, ["--target", "my_aio_func"])

    assert create_asgi_app.calls == [pretend.call("my_aio_func", None, "http")]
    assert asgi_server.run.calls == [pretend.call("0.0.0.0", 8080)]
    
    _function_registry.ASGI_FUNCTIONS.clear()
    _function_registry.ASGI_FUNCTIONS.update(original_asgi_functions)


def test_no_auto_asgi_for_regular_functions(monkeypatch):
    original_asgi_functions = _function_registry.ASGI_FUNCTIONS.copy()
    _function_registry.ASGI_FUNCTIONS.clear()

    app = pretend.stub()
    create_app = pretend.call_recorder(lambda *a, **k: app)
    monkeypatch.setattr(functions_framework._cli, "create_app", create_app)

    flask_server = pretend.stub(run=pretend.call_recorder(lambda host, port: None))
    create_server = pretend.call_recorder(lambda app, debug: flask_server)
    monkeypatch.setattr(functions_framework._cli, "create_server", create_server)

    runner = CliRunner()
    result = runner.invoke(_cli, ["--target", "regular_func"])

    assert create_app.calls == [pretend.call("regular_func", None, "http")]
    assert flask_server.run.calls == [pretend.call("0.0.0.0", 8080)]
    
    _function_registry.ASGI_FUNCTIONS.clear()
    _function_registry.ASGI_FUNCTIONS.update(original_asgi_functions)
