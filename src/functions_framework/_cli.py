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

from functions_framework import _function_registry, create_app
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
def _cli(target, source, signature_type, host, port, debug, asgi):
    if asgi:
        from functions_framework.aio import create_asgi_app

        app = create_asgi_app(target, source, signature_type)
    else:
        app = create_app(target, source, signature_type)
    create_server(app, debug).run(host, port)
