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
import pytest

from click.testing import CliRunner

import functions_framework

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
            ["--target", "foo", "--dry-run"],
            {},
            [pretend.call("foo", None, "http")],
            [],
        ),
        (
            [],
            {"FUNCTION_TARGET": "foo", "DRY_RUN": "True"},
            [pretend.call("foo", None, "http")],
            [],
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
