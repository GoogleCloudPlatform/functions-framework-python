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
import pathlib
import socket
import time

from multiprocessing import Process

import pytest
import requests

ff_gunicorn = pytest.importorskip("functions_framework._http.gunicorn")


from functions_framework import create_app

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"
TEST_HOST = "0.0.0.0"
TEST_PORT = "8080"


@pytest.fixture(autouse=True)
def run_around_tests():
    # the test samples test also listens on 8080, so let's be good stewards of
    # the port and make sure it's free
    _wait_for_no_listen(TEST_HOST, TEST_PORT)
    yield
    _wait_for_no_listen(TEST_HOST, TEST_PORT)


@pytest.mark.skipif("platform.system() == 'Windows'")
@pytest.mark.skipif("platform.system() == 'Darwin'")
@pytest.mark.slow_integration_test
def test_no_timeout_allows_request_processing_to_finish():
    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    options = {}

    gunicorn_app = ff_gunicorn.GunicornApplication(
        app, TEST_HOST, TEST_PORT, False, **options
    )

    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_listen(TEST_HOST, TEST_PORT)

    result = requests.get("http://{}:{}/".format(TEST_HOST, TEST_PORT))

    gunicorn_p.terminate()
    gunicorn_p.join()

    assert result.status_code == 200


@pytest.mark.skipif("platform.system() == 'Windows'")
@pytest.mark.skipif("platform.system() == 'Darwin'")
@pytest.mark.slow_integration_test
def test_timeout_but_not_threaded_timeout_enabled_does_not_kill(monkeypatch):
    monkeypatch.setenv("CLOUD_RUN_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("THREADED_TIMEOUT_ENABLED", "false")
    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    options = {}

    gunicorn_app = ff_gunicorn.GunicornApplication(
        app, TEST_HOST, TEST_PORT, False, **options
    )

    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_listen(TEST_HOST, TEST_PORT)

    result = requests.get("http://{}:{}/".format(TEST_HOST, TEST_PORT))

    gunicorn_p.terminate()
    gunicorn_p.join()

    assert result.status_code == 200


@pytest.mark.skipif("platform.system() == 'Windows'")
@pytest.mark.skipif("platform.system() == 'Darwin'")
@pytest.mark.slow_integration_test
def test_timeout_and_threaded_timeout_enabled_kills(monkeypatch):
    monkeypatch.setenv("CLOUD_RUN_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("THREADED_TIMEOUT_ENABLED", "true")
    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    options = {}

    gunicorn_app = ff_gunicorn.GunicornApplication(
        app, TEST_HOST, TEST_PORT, False, **options
    )

    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_listen(TEST_HOST, TEST_PORT)

    result = requests.get("http://{}:{}/".format(TEST_HOST, TEST_PORT))

    gunicorn_p.terminate()
    gunicorn_p.join()

    # Any exception raised in execution is a 500 error. Cloud Functions 1st gen and
    # 2nd gen/Cloud Run infrastructure doing the timeout will return a 408 (gen 1)
    # or 504 (gen 2/CR) at the infrastructure layer when request timeouts happen,
    # and this code will only be available to the user in logs.
    assert result.status_code == 500


@pytest.mark.skipif("platform.system() == 'Windows'")
@pytest.mark.skipif("platform.system() == 'Darwin'")
@pytest.mark.slow_integration_test
def test_timeout_and_threaded_timeout_enabled_but_timeout_not_exceeded_doesnt_kill(
    monkeypatch,
):
    monkeypatch.setenv("CLOUD_RUN_TIMEOUT_SECONDS", "2")
    monkeypatch.setenv("THREADED_TIMEOUT_ENABLED", "true")
    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    options = {}

    gunicorn_app = ff_gunicorn.GunicornApplication(
        app, TEST_HOST, TEST_PORT, False, **options
    )

    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_listen(TEST_HOST, TEST_PORT)

    result = requests.get("http://{}:{}/".format(TEST_HOST, TEST_PORT))

    gunicorn_p.terminate()
    gunicorn_p.join()

    assert result.status_code == 200


@pytest.mark.skipif("platform.system() == 'Windows'")
@pytest.mark.skipif("platform.system() == 'Darwin'")
@pytest.mark.slow_integration_test
def test_timeout_sync_worker_kills_on_timeout(
    monkeypatch,
):
    monkeypatch.setenv("CLOUD_RUN_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WORKERS", 2)
    monkeypatch.setenv("THREADS", 1)
    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    options = {}

    gunicorn_app = ff_gunicorn.GunicornApplication(
        app, TEST_HOST, TEST_PORT, False, **options
    )

    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_listen(TEST_HOST, TEST_PORT)

    result = requests.get("http://{}:{}/".format(TEST_HOST, TEST_PORT))

    gunicorn_p.terminate()
    gunicorn_p.join()

    assert result.status_code == 500


@pytest.mark.skipif("platform.system() == 'Windows'")
@pytest.mark.skipif("platform.system() == 'Darwin'")
@pytest.mark.slow_integration_test
def test_timeout_sync_worker_does_not_kill_if_less_than_timeout(
    monkeypatch,
):
    monkeypatch.setenv("CLOUD_RUN_TIMEOUT_SECONDS", "2")
    monkeypatch.setenv("WORKERS", 2)
    monkeypatch.setenv("THREADS", 1)
    source = TEST_FUNCTIONS_DIR / "timeout" / "main.py"
    target = "function"

    app = create_app(target, source)

    options = {}

    gunicorn_app = ff_gunicorn.GunicornApplication(
        app, TEST_HOST, TEST_PORT, False, **options
    )

    gunicorn_p = Process(target=gunicorn_app.run)
    gunicorn_p.start()

    _wait_for_listen(TEST_HOST, TEST_PORT)

    result = requests.get("http://{}:{}/".format(TEST_HOST, TEST_PORT))

    gunicorn_p.terminate()
    gunicorn_p.join()

    assert result.status_code == 200


@pytest.mark.skip
def _wait_for_listen(host, port, timeout=10):
    # Used in tests to make sure that the gunicorn app has booted and is
    # listening before sending a test request
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError(
                    "Waited too long for port {} on host {} to start accepting "
                    "connections.".format(port, host)
                ) from ex


@pytest.mark.skip
def _wait_for_no_listen(host, port, timeout=10):
    # Used in tests to make sure that the port is actually free after
    # the process binding to it should have been killed
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                time.sleep(0.01)
                if time.perf_counter() - start_time >= timeout:
                    raise TimeoutError(
                        "Waited too long for port {} on host {} to stop accepting "
                        "connections.".format(port, host)
                    )
        except OSError as ex:
            break
