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

import flask
import pretend
import pytest

from starlette.applications import Starlette

import functions_framework._http


def test_httpserver_detects_asgi_app():
    flask_app = flask.Flask("test")
    flask_wrapper = functions_framework._http.HTTPServer(flask_app, debug=True)
    assert flask_wrapper.server_class.__name__ == "FlaskApplication"

    starlette_app = Starlette(routes=[])
    starlette_wrapper = functions_framework._http.HTTPServer(starlette_app, debug=True)
    assert starlette_wrapper.server_class.__name__ == "StarletteApplication"


@pytest.mark.skipif("platform.system() == 'Windows'")
def test_httpserver_production_asgi():
    starlette_app = Starlette(routes=[])
    wrapper = functions_framework._http.HTTPServer(starlette_app, debug=False)
    assert wrapper.server_class.__name__ == "UvicornApplication"


def test_starlette_application_init():
    from functions_framework._http.asgi import StarletteApplication

    app = pretend.stub()
    host = "1.2.3.4"
    port = "5678"

    # Test debug mode
    starlette_app = StarletteApplication(app, host, port, debug=True, custom="value")
    assert starlette_app.app == app
    assert starlette_app.host == host
    assert starlette_app.port == port
    assert starlette_app.debug is True
    assert starlette_app.options["log_level"] == "debug"
    assert starlette_app.options["custom"] == "value"

    # Test production mode
    starlette_app = StarletteApplication(app, host, port, debug=False)
    assert starlette_app.options["log_level"] == "error"


@pytest.mark.skipif("platform.system() == 'Windows'")
def test_uvicorn_application_init():
    from functions_framework._http.gunicorn import UvicornApplication

    app = pretend.stub()
    host = "1.2.3.4"
    port = "1234"

    uvicorn_app = UvicornApplication(app, host, port, debug=False)
    assert uvicorn_app.app == app
    assert uvicorn_app.options["worker_class"] == "uvicorn_worker.UvicornWorker"
    assert uvicorn_app.options["bind"] == "1.2.3.4:1234"
    assert uvicorn_app.load() == app


def test_httpserver_fallback_on_import_error(monkeypatch):
    starlette_app = Starlette(routes=[])

    monkeypatch.setitem(sys.modules, "functions_framework._http.gunicorn", None)

    wrapper = functions_framework._http.HTTPServer(starlette_app, debug=False)
    assert wrapper.server_class.__name__ == "StarletteApplication"


def test_starlette_application_run(monkeypatch):
    uvicorn_run_calls = []

    def mock_uvicorn_run(app, **kwargs):
        uvicorn_run_calls.append((app, kwargs))

    uvicorn_stub = pretend.stub(run=mock_uvicorn_run)
    monkeypatch.setitem(sys.modules, "uvicorn", uvicorn_stub)

    # Clear and re-import to get fresh module with mocked uvicorn
    if "functions_framework._http.asgi" in sys.modules:
        del sys.modules["functions_framework._http.asgi"]

    from functions_framework._http.asgi import StarletteApplication

    app = pretend.stub()
    host = "1.2.3.4"
    port = "5678"

    starlette_app = StarletteApplication(app, host, port, debug=True, custom="value")
    starlette_app.run()

    assert len(uvicorn_run_calls) == 1
    assert uvicorn_run_calls[0][0] == app
    assert uvicorn_run_calls[0][1] == {
        "host": host,
        "port": int(port),
        "log_level": "debug",
        "custom": "value",
    }
