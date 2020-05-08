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

import platform
import sys

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
    app = pretend.stub()
    http_server = pretend.stub(run=pretend.call_recorder(lambda: None))
    server_classes = {
        "flask": pretend.call_recorder(lambda *a, **kw: http_server),
        "gunicorn": pretend.call_recorder(lambda *a, **kw: http_server),
    }
    options = {"a": pretend.stub(), "b": pretend.stub()}

    monkeypatch.setattr(
        functions_framework._http, "FlaskApplication", server_classes["flask"],
    )
    if gunicorn_missing or platform.system() == "Windows":
        monkeypatch.setitem(sys.modules, "functions_framework._http.gunicorn", None)
    else:
        from functions_framework._http import gunicorn

        monkeypatch.setattr(
            gunicorn, "GunicornApplication", server_classes["gunicorn"],
        )

    wrapper = functions_framework._http.HTTPServer(app, debug, **options)

    assert wrapper.app == app
    assert wrapper.server_class == server_classes[expected]
    assert wrapper.options == options

    host = pretend.stub()
    port = pretend.stub()

    wrapper.run(host, port)

    assert wrapper.server_class.calls == [pretend.call(app, host, port, **options)]
    assert http_server.run.calls == [pretend.call()]


@pytest.mark.skipif("platform.system() == 'Windows'")
def test_gunicorn_application():
    app = pretend.stub()
    host = "1.2.3.4"
    port = "1234"
    options = {}

    import functions_framework._http.gunicorn

    gunicorn_app = functions_framework._http.gunicorn.GunicornApplication(
        app, host, port, **options
    )

    assert gunicorn_app.app == app
    assert gunicorn_app.options == {
        "bind": "%s:%s" % (host, port),
        "workers": 1,
        "threads": 8,
        "timeout": 0,
    }

    assert gunicorn_app.cfg.bind == ["1.2.3.4:1234"]
    assert gunicorn_app.cfg.workers == 1
    assert gunicorn_app.cfg.threads == 8
    assert gunicorn_app.cfg.timeout == 0
    assert gunicorn_app.load() == app


def test_flask_application():
    app = pretend.stub(run=pretend.call_recorder(lambda *a, **kw: None))
    host = pretend.stub()
    port = pretend.stub()
    options = {"a": pretend.stub(), "b": pretend.stub()}

    flask_app = functions_framework._http.flask.FlaskApplication(
        app, host, port, **options
    )

    assert flask_app.app == app
    assert flask_app.host == host
    assert flask_app.port == port
    assert flask_app.options == options

    flask_app.run()

    assert app.run.calls == [
        pretend.call(host, port, debug=True, a=options["a"], b=options["b"]),
    ]
