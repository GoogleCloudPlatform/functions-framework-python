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
import platform
import sys

import flask
import pretend
import pytest

import functions_framework._http


@pytest.mark.parametrize("debug", [True, False])
def test_create_server(monkeypatch, debug):
    server_stub = pretend.stub()
    httpserver = pretend.call_recorder(lambda *a, **kw: server_stub)
    monkeypatch.setattr(functions_framework._http, "HTTPServer", httpserver)
    wsgi_app = pretend.stub()
    options = {"a": pretend.stub(), "b": pretend.stub()}

    functions_framework._http.create_server(wsgi_app, debug, **options)

    assert httpserver.calls == [pretend.call(wsgi_app, debug, **options)]


@pytest.mark.parametrize(
    "debug, gunicorn_missing, expected",
    [
        (True, False, "flask"),
        (False, False, "flask" if platform.system() == "Windows" else "gunicorn"),
        (True, True, "flask"),
        (False, True, "flask"),
    ],
)
def test_httpserver(monkeypatch, debug, gunicorn_missing, expected):
    app = flask.Flask("test")
    http_server = pretend.stub(run=pretend.call_recorder(lambda: None))
    server_classes = {
        "flask": pretend.call_recorder(lambda *a, **kw: http_server),
        "gunicorn": pretend.call_recorder(lambda *a, **kw: http_server),
    }
    options = {"a": pretend.stub(), "b": pretend.stub()}

    monkeypatch.setattr(
        functions_framework._http, "FlaskApplication", server_classes["flask"]
    )
    if gunicorn_missing or platform.system() == "Windows":
        monkeypatch.setitem(sys.modules, "functions_framework._http.gunicorn", None)
    else:
        from functions_framework._http import gunicorn

        monkeypatch.setattr(gunicorn, "GunicornApplication", server_classes["gunicorn"])

    wrapper = functions_framework._http.HTTPServer(app, debug, **options)

    assert wrapper.app == app
    assert wrapper.server_class == server_classes[expected]
    assert wrapper.options == options

    host = pretend.stub()
    port = pretend.stub()

    wrapper.run(host, port)

    assert wrapper.server_class.calls == [
        pretend.call(app, host, port, debug, **options)
    ]
    assert http_server.run.calls == [pretend.call()]


@pytest.mark.skipif("platform.system() == 'Windows'")
@pytest.mark.parametrize("debug", [True, False])
def test_gunicorn_application(debug):
    app = pretend.stub()
    host = "1.2.3.4"
    port = "1234"
    options = {}

    import functions_framework._http.gunicorn

    gunicorn_app = functions_framework._http.gunicorn.GunicornApplication(
        app, host, port, debug, **options
    )

    assert gunicorn_app.app == app
    assert gunicorn_app.options == {
        "bind": "%s:%s" % (host, port),
        "workers": 1,
        "threads": os.cpu_count() * 4,
        "timeout": 0,
        "loglevel": "error",
        "limit_request_line": 0,
    }

    assert gunicorn_app.cfg.bind == ["1.2.3.4:1234"]
    assert gunicorn_app.cfg.workers == 1
    assert gunicorn_app.cfg.threads == os.cpu_count() * 4
    assert gunicorn_app.cfg.timeout == 0
    assert gunicorn_app.load() == app


@pytest.mark.parametrize("debug", [True, False])
def test_flask_application(debug):
    app = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    host = pretend.stub()
    port = pretend.stub()
    options = {"a": pretend.stub(), "b": pretend.stub()}

    flask_app = functions_framework._http.flask.FlaskApplication(
        app, host, port, debug, **options
    )

    assert flask_app.app == app
    assert flask_app.host == host
    assert flask_app.port == port
    assert flask_app.debug == debug
    assert flask_app.options == options

    flask_app.run()

    assert app.run.calls == [
        pretend.call(host, port, debug=debug, a=options["a"], b=options["b"]),
    ]


@pytest.mark.parametrize(
    "debug, uvicorn_missing, expected",
    [
        (True, False, "starlette"),
        (False, False, "uvicorn" if platform.system() != "Windows" else "starlette"),
        (True, True, "starlette"),
        (False, True, "starlette"),
    ],
)
def test_httpserver_asgi(monkeypatch, debug, uvicorn_missing, expected):
    app = pretend.stub()
    http_server = pretend.stub(run=pretend.call_recorder(lambda: None))
    server_classes = {
        "starlette": pretend.call_recorder(lambda *a, **kw: http_server),
        "uvicorn": pretend.call_recorder(lambda *a, **kw: http_server),
    }
    options = {"a": pretend.stub(), "b": pretend.stub()}

    from functions_framework._http import asgi

    monkeypatch.setattr(asgi, "StarletteApplication", server_classes["starlette"])

    if uvicorn_missing or platform.system() == "Windows":
        monkeypatch.setitem(sys.modules, "functions_framework._http.gunicorn", None)
    else:
        from functions_framework._http import gunicorn

        monkeypatch.setattr(gunicorn, "UvicornApplication", server_classes["uvicorn"])

    wrapper = functions_framework._http.HTTPServer(app, debug, **options)

    assert wrapper.app == app
    assert wrapper.server_class == server_classes[expected]
    assert wrapper.options == options

    host = pretend.stub()
    port = pretend.stub()

    wrapper.run(host, port)

    assert wrapper.server_class.calls == [
        pretend.call(app, host, port, debug, **options)
    ]
    assert http_server.run.calls == [pretend.call()]


@pytest.mark.skipif("platform.system() == 'Windows'")
def test_uvicorn_application():
    app = pretend.stub()
    host = "1.2.3.4"
    port = "1234"
    options = {}

    import functions_framework._http.gunicorn

    uvicorn_app = functions_framework._http.gunicorn.UvicornApplication(
        app, host, port, debug=False, **options
    )

    assert uvicorn_app.app == app
    assert uvicorn_app.options == {
        "bind": "%s:%s" % (host, port),
        "workers": 1,
        "timeout": 0,
        "loglevel": "error",
        "limit_request_line": 0,
        "worker_class": "uvicorn_worker.UvicornWorker",
    }

    assert uvicorn_app.cfg.bind == ["1.2.3.4:1234"]
    assert uvicorn_app.cfg.workers == 1
    assert uvicorn_app.cfg.timeout == 0
    assert uvicorn_app.load() == app


@pytest.mark.parametrize("debug", [True, False])
def test_starlette_application(monkeypatch, debug):
    uvicorn_run = pretend.call_recorder(lambda *a, **kw: None)
    uvicorn_stub = pretend.stub(run=uvicorn_run)
    monkeypatch.setitem(sys.modules, "uvicorn", uvicorn_stub)

    # Clear and re-import to get fresh module with mocked uvicorn
    if "functions_framework._http.asgi" in sys.modules:
        del sys.modules["functions_framework._http.asgi"]

    from functions_framework._http.asgi import StarletteApplication

    app = pretend.stub()
    host = "1.2.3.4"
    port = "5678"
    options = {"custom": "value"}

    starlette_app = StarletteApplication(app, host, port, debug, **options)

    assert starlette_app.app == app
    assert starlette_app.host == host
    assert starlette_app.port == port
    assert starlette_app.debug == debug
    assert starlette_app.options == {
        "log_level": "debug" if debug else "error",
        "custom": "value",
    }

    starlette_app.run()

    assert uvicorn_run.calls == [
        pretend.call(
            app,
            host=host,
            port=int(port),
            log_level="debug" if debug else "error",
            custom="value",
        )
    ]
