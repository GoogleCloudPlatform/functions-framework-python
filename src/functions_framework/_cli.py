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

import click

from functions_framework import _function_registry, create_app
from functions_framework._http import create_server


def _parse_env_file(file_path):
    """Parse a .env file and return a dict of key-value pairs.

    Supports lines of the form KEY=VALUE. Lines starting with '#' and blank
    lines are skipped. Values may be optionally quoted with single or double
    quotes.
    """
    env_vars = {}
    path = pathlib.Path(file_path)
    if not path.is_file():
        raise click.BadParameter(
            f"env file '{file_path}' does not exist",
            param_hint="--env-file",
        )
    for lineno, raw_line in enumerate(path.read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not key or not sep:
            raise click.BadParameter(
                f"invalid format on line {lineno}: must be KEY=VALUE",
                param_hint="--env-file",
            )
        # Strip optional surrounding quotes
        value = value.strip()
        if len(value) >= 2 and (
            (value[0] == '"' and value[-1] == '"')
            or (value[0] == "'" and value[-1] == "'")
        ):
            value = value[1:-1]
        env_vars[key.strip()] = value
    return env_vars


@click.command()
@click.option("--target", envvar="FUNCTION_TARGET", type=click.STRING, required=True)
@click.option("--source", envvar="FUNCTION_SOURCE", type=click.Path(), default=None)
@click.option(
    "--signature-type",
    envvar="FUNCTION_SIGNATURE_TYPE",
    type=click.Choice(["http", "event", "cloudevent", "typed"]),
    default="http",
)
@click.option("--host", envvar="HOST", type=click.STRING, default="0.0.0.0")
@click.option("--port", envvar="PORT", type=click.INT, default=8080)
@click.option("--debug", envvar="DEBUG", is_flag=True)
@click.option(
    "--env",
    "env_vars",
    multiple=True,
    metavar="KEY=VALUE",
    help="Set a runtime environment variable for local execution. Repeatable.",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="Load runtime environment variables from a .env file.",
)
@click.option(
    "--asgi",
    envvar="FUNCTION_USE_ASGI",
    is_flag=True,
    help="Use ASGI server for function execution",
)
def _cli(target, source, signature_type, host, port, debug, env_vars, env_file, asgi):
    # Apply environment variables from --env-file first, then --env overrides
    if env_file:
        file_vars = _parse_env_file(env_file)
        os.environ.update(file_vars)

    for env_var in env_vars:
        key, separator, value = env_var.partition("=")
        if not key or not separator:
            raise click.BadParameter(
                "must be in KEY=VALUE format", param_hint="--env"
            )
        os.environ[key] = value

    if asgi:
        from functions_framework.aio import create_asgi_app

        app = create_asgi_app(target, source, signature_type)
    else:
        app = create_app(target, source, signature_type)
    create_server(app, debug).run(host, port)
