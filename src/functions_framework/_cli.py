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

import click

from functions_framework import create_app
from functions_framework._http import create_server


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
    "--asgi",
    envvar="FUNCTION_USE_ASGI",
    is_flag=True,
    help="Use ASGI server for function execution",
)
@click.option(
    "--env",
    multiple=True,
    help="Set environment variables (can be used multiple times): --env KEY=VALUE",
)
@click.option(
    "--env-file",
    multiple=True,
    type=click.Path(exists=True),
    help="Path(s) to file(s) containing environment variables (KEY=VALUE format)",
)
def _cli(target, source, signature_type, host, port, debug, asgi, env, env_file):
    # Load environment variables from all provided --env-file arguments
    for file_path in env_file:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Skip comments and blank lines
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
                else:
                    raise click.BadParameter(f"Invalid line in env-file '{file_path}': {line}")

    # Load environment variables from all --env flags
    for item in env:
        if "=" in item:
            key, value = item.split("=", 1)
            os.environ[key.strip()] = value.strip()
        else:
            raise click.BadParameter(f"Invalid --env format: '{item}'. Expected KEY=VALUE.")

    # Launch ASGI or WSGI server
    if asgi:  # pragma: no cover
        from functions_framework.aio import create_asgi_app
        app = create_asgi_app(target, source, signature_type)
    else:
        app = create_app(target, source, signature_type)

    create_server(app, debug).run(host, port)
