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

from functions_framework.cli import cli


@pytest.fixture
def create_app(monkeypatch):
    create_app = pretend.call_recorder(
        lambda *a, **kw: pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    )
    monkeypatch.setattr(functions_framework.cli, "create_app", create_app)
    return create_app


def test_cli_no_arguments():
    runner = CliRunner()
    result = runner.invoke(cli)

    assert result.exit_code == 2
    assert 'Missing option "--target"' in result.output


@pytest.mark.parametrize(
    "args, env, call",
    [
        (["--target", "foo"], {}, pretend.call("foo", None, "http")),
        ([], {"FUNCTION_TARGET": "foo"}, pretend.call("foo", None, "http")),
        (
            ["--target", "foo", "--source", "/path/to/source.py"],
            {},
            pretend.call("foo", "/path/to/source.py", "http"),
        ),
        (
            [],
            {"FUNCTION_TARGET": "foo", "FUNCTION_SOURCE": "/path/to/source.py"},
            pretend.call("foo", "/path/to/source.py", "http"),
        ),
        (
            ["--target", "foo", "--signature-type", "event"],
            {},
            pretend.call("foo", None, "event"),
        ),
        (
            [],
            {"FUNCTION_TARGET": "foo", "FUNCTION_SIGNATURE_TYPE": "event"},
            pretend.call("foo", None, "event"),
        ),
    ],
)
def test_cli_arguments(create_app, args, env, call):
    runner = CliRunner(env=env)
    result = runner.invoke(cli, args)

    if result.output:
        print(result.output)

    assert result.exit_code == 0
    assert create_app.calls == [call]
