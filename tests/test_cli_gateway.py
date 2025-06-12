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

import sys

import pretend
import pytest

from click.testing import CliRunner

from functions_framework._cli import _cli as cli_command


# Test for CLI gateway flag
def test_cli_gateway_default(monkeypatch):
    """Test default gateway is WSGI"""
    server = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    app = pretend.stub()

    create_app = pretend.call_recorder(lambda *a, **kw: app)
    create_server = pretend.call_recorder(lambda *a, **kw: server)

    from functions_framework import _cli

    monkeypatch.setattr(_cli, "create_app", create_app)
    monkeypatch.setattr(_cli, "create_server", create_server)

    runner = CliRunner()
    result = runner.invoke(cli_command, ["--target", "foo"])

    assert result.exit_code == 0
    assert create_app.calls == [pretend.call("foo", None, "http")]
    assert server.run.calls == [pretend.call("0.0.0.0", 8080)]


def test_cli_gateway_wsgi_explicit(monkeypatch):
    """Test explicit --gateway wsgi"""
    server = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    app = pretend.stub()

    create_app = pretend.call_recorder(lambda *a, **kw: app)
    create_server = pretend.call_recorder(lambda *a, **kw: server)

    from functions_framework import _cli

    monkeypatch.setattr(_cli, "create_app", create_app)
    monkeypatch.setattr(_cli, "create_server", create_server)

    runner = CliRunner()
    result = runner.invoke(cli_command, ["--target", "foo", "--gateway", "wsgi"])

    assert result.exit_code == 0
    assert create_app.calls == [pretend.call("foo", None, "http")]


def test_cli_gateway_asgi(monkeypatch):
    """Test --gateway asgi"""
    # Skip this test if aio module is not available
    try:
        import functions_framework.aio
    except ImportError:
        pytest.skip("Async support not available")

    server = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    app = pretend.stub()

    # Mock the create_asgi_app function
    create_asgi_app = pretend.call_recorder(lambda *a, **kw: app)
    monkeypatch.setattr("functions_framework.aio.create_asgi_app", create_asgi_app)

    create_server = pretend.call_recorder(lambda *a, **kw: server)

    from functions_framework import _cli

    monkeypatch.setattr(_cli, "create_server", create_server)

    runner = CliRunner()
    result = runner.invoke(cli_command, ["--target", "foo", "--gateway", "asgi"])

    assert result.exit_code == 0
    assert create_asgi_app.calls == [pretend.call("foo", None, "http")]


def test_cli_gateway_asgi_cloudevent(monkeypatch):
    """Test --gateway asgi with cloudevent signature"""
    # Skip this test if aio module is not available
    try:
        import functions_framework.aio
    except ImportError:
        pytest.skip("Async support not available")

    server = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    app = pretend.stub()

    # Mock the create_asgi_app function
    create_asgi_app = pretend.call_recorder(lambda *a, **kw: app)
    monkeypatch.setattr("functions_framework.aio.create_asgi_app", create_asgi_app)

    create_server = pretend.call_recorder(lambda *a, **kw: server)

    from functions_framework import _cli

    monkeypatch.setattr(_cli, "create_server", create_server)

    runner = CliRunner()
    result = runner.invoke(
        cli_command,
        ["--target", "foo", "--gateway", "asgi", "--signature-type", "cloudevent"],
    )

    assert result.exit_code == 0
    assert create_asgi_app.calls == [pretend.call("foo", None, "cloudevent")]


def test_cli_gateway_env_var(monkeypatch):
    """Test GATEWAY environment variable"""
    # Skip this test if aio module is not available
    try:
        import functions_framework.aio
    except ImportError:
        pytest.skip("Async support not available")

    server = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    app = pretend.stub()

    # Mock the create_asgi_app function
    create_asgi_app = pretend.call_recorder(lambda *a, **kw: app)
    monkeypatch.setattr("functions_framework.aio.create_asgi_app", create_asgi_app)

    create_server = pretend.call_recorder(lambda *a, **kw: server)

    from functions_framework import _cli

    monkeypatch.setattr(_cli, "create_server", create_server)

    runner = CliRunner(env={"GATEWAY": "asgi"})
    result = runner.invoke(cli_command, ["--target", "foo"])

    assert result.exit_code == 0
    assert create_asgi_app.calls == [pretend.call("foo", None, "http")]


def test_cli_invalid_gateway():
    """Test that invalid gateway values are rejected"""
    runner = CliRunner()
    result = runner.invoke(cli_command, ["--target", "foo", "--gateway", "invalid"])

    assert result.exit_code == 2
    assert "Invalid value" in result.output
    assert "'invalid' is not one of 'wsgi', 'asgi'" in result.output
