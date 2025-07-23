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
import sys

import pretend
import pytest

from click.testing import CliRunner

import functions_framework
import functions_framework._function_registry as _function_registry

from functions_framework._cli import _cli

# Conditional import for Starlette (Python 3.8+)
if sys.version_info >= (3, 8):
    from starlette.applications import Starlette
else:
    Starlette = None


@pytest.fixture(autouse=True)
def clean_registries():
    """Clean up both REGISTRY_MAP and ASGI_FUNCTIONS registries."""
    original_registry_map = _function_registry.REGISTRY_MAP.copy()
    original_asgi = _function_registry.ASGI_FUNCTIONS.copy()
    _function_registry.REGISTRY_MAP.clear()
    _function_registry.ASGI_FUNCTIONS.clear()
    yield
    _function_registry.REGISTRY_MAP.clear()
    _function_registry.REGISTRY_MAP.update(original_registry_map)
    _function_registry.ASGI_FUNCTIONS.clear()
    _function_registry.ASGI_FUNCTIONS.update(original_asgi)


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


def test_cli_auto_detects_asgi_decorator():
    """Test that CLI auto-detects @aio decorated functions without --asgi flag."""
    # Use the actual async_decorator.py test file which has @aio.http decorated functions
    test_functions_dir = pathlib.Path(__file__).parent / "test_functions" / "decorators"
    source = test_functions_dir / "async_decorator.py"

    # Call create_app without any asgi flag - should auto-detect
    app = functions_framework.create_app(target="function_http", source=str(source))

    # Verify it created a Starlette app (ASGI)
    assert isinstance(app, Starlette)

    # Verify the function was registered in ASGI_FUNCTIONS
    assert "function_http" in _function_registry.ASGI_FUNCTIONS
