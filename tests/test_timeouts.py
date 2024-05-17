# Copyright 2024 Google LLC
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
import pytest
import requests
import socket
import time

from multiprocessing import Process

import functions_framework._http.gunicorn
from functions_framework import create_app

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"


@pytest.mark.skip
def test_no_timeout_allows_request_processing_to_finish():
    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    host = "0.0.0.0"
    port = "8080"
    options = {}

    gunicorn_app = functions_framework._http.gunicorn.GunicornApplication(
        app, host, port, False, **options
    )

    os.environ.clear()

    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_port(host, port)

    result = requests.get("http://{}:{}/".format(host, port))

    gunicorn_p.kill()

    assert result.status_code == 200


@pytest.mark.skip
def test_timeout_but_not_threaded_timeout_enabled_does_not_kill():

    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    host = "0.0.0.0"
    port = "8081"
    options = {}

    gunicorn_app = functions_framework._http.gunicorn.GunicornApplication(
        app, host, port, False, **options
    )

    os.environ.clear()
    os.environ['CLOUD_RUN_TIMEOUT_SECONDS'] = "1"
    os.environ['THREADED_TIMEOUT_ENABLED'] = "false"

    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_port(host, port)

    result = requests.get("http://{}:{}/".format(host, port))

    gunicorn_p.kill()

    assert result.status_code == 200


def test_timeout_and_threaded_timeout_enabled_kills(monkeypatch):
    monkeypatch.setenv('CLOUD_RUN_TIMEOUT_SECONDS', 1)
    monkeypatch.setenv('THREADED_TIMEOUT_ENABLED', "true")
    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    host = "0.0.0.0"
    port = "8082"
    options = {}

    gunicorn_app = functions_framework._http.gunicorn.GunicornApplication(
        app, host, port, False, **options
    )

    gunicorn_app.run()
    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_port(host, port)

    result = requests.get("http://{}:{}/".format(host, port))

    gunicorn_p.kill()

    assert (
        result.status_code == 500
    )  # TODO: this should be 504, where do i have to translate this?


def test_timeout_and_threaded_timeout_enabled_but_timeout_not_exceeded_doesnt_kill(monkeypatch):
    monkeypatch.setenv('CLOUD_RUN_TIMEOUT_SECONDS', "2")
    monkeypatch.setenv('THREADED_TIMEOUT_ENABLED', "true")
    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    host = "0.0.0.0"
    port = "8083"
    options = {}

    gunicorn_app = functions_framework._http.gunicorn.GunicornApplication(
        app, host, port, False, **options
    )

    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_port(host, port)

    result = requests.get("http://{}:{}/".format(host, port))

    gunicorn_p.kill()

    assert result.status_code == 200


@pytest.mark.skip
def _wait_for_port(host, port, timeout=10):
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError(
                    "Waited too long for the port {} on host {} to start accepting "
                    "connections.".format(port, host)
                ) from ex