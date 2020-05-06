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

import functions_framework._http

stub = pretend.stub()


def test_create_server(monkeypatch):
    server_stub = pretend.stub()
    httpserver = pretend.call_recorder(lambda *a, **kw: server_stub)
    monkeypatch.setattr(functions_framework._http, "HTTPServer", httpserver)
    wsgi_app = pretend.stub()
    options = {"a": pretend.stub(), "b": pretend.stub()}

    functions_framework._http.create_server(wsgi_app, **options)

    assert httpserver.calls == [
        pretend.call(
            wsgi_app,
            server_class=functions_framework._http.GunicornApplication,
            **options
        )
    ]


def test_httpserver():
    app = pretend.stub()
    http_server = pretend.stub(run=pretend.call_recorder(lambda: None))
    server_class = pretend.call_recorder(lambda *a, **kw: http_server)
    options = {"a": pretend.stub(), "b": pretend.stub()}

    wrapper = functions_framework._http.HTTPServer(app, server_class, **options)

    assert wrapper.app == app
    assert wrapper.server_class == server_class
    assert wrapper.options == options

    host = pretend.stub()
    port = pretend.stub()

    wrapper.run(host, port)

    assert server_class.calls == [pretend.call(app, host, port, **options)]
    assert http_server.run.calls == [pretend.call()]


def test_gunicorn_application(monkeypatch):
    app = pretend.stub()
    host = "1.2.3.4"
    port = "1234"
    options = {}

    gunicorn_app = functions_framework._http.GunicornApplication(
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
