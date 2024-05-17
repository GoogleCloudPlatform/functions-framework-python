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

import gunicorn.app.base

from gunicorn.workers.gthread import ThreadWorker

from ..request_timeout import ThreadingTimeout

# global for use in our custom gthread worker; the gunicorn arbiter spawns these
# and it's not possible to inject (and self.timeout means something different to
# async workers!)
# set/managed in gunicorn application init for test-friendliness
TIMEOUT_SECONDS = None


class GunicornApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, host, port, debug, **options):
        threads = int(os.environ.get("THREADS", (os.cpu_count() or 1) * 4))

        global TIMEOUT_SECONDS
        TIMEOUT_SECONDS = int(os.environ.get("CLOUD_RUN_TIMEOUT_SECONDS", 0))

        self.options = {
            "bind": "%s:%s" % (host, port),
            "workers": int(os.environ.get("WORKERS", 1)),
            "threads": threads,
            "loglevel": os.environ.get("GUNICORN_LOG_LEVEL", "error"),
            "limit_request_line": 0,
        }

        if (
            TIMEOUT_SECONDS > 0
            and threads > 1
            and (os.environ.get("THREADED_TIMEOUT_ENABLED", "False").lower() == "true")
        ):  # pragma: no cover
            self.options["worker_class"] = (
                "functions_framework._http.gunicorn.GThreadWorkerWithTimeoutSupport"
            )
        else:
            self.options["timeout"] = TIMEOUT_SECONDS

        self.options.update(options)
        self.app = app

        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.app


class GThreadWorkerWithTimeoutSupport(ThreadWorker):  # pragma: no cover
    def handle_request(self, req, conn):
        with ThreadingTimeout(TIMEOUT_SECONDS):
            super(GThreadWorkerWithTimeoutSupport, self).handle_request(req, conn)
