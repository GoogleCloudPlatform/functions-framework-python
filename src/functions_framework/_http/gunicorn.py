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

import gunicorn.app.base


class GunicornApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, workers, threads, host, port, timeout, debug,
        **options):
        self.options = {
            "bind": "%s:%s" % (host, port),
            "workers": workers,
            "threads": threads,
            "timeout": timeout or os.environ.get("K_TIMEOUT_SECONDS", 0),
            "loglevel": "error",
            "limit_request_line": 0,
        }
        print(self.options)
        self.options.update(options)
        self.app = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.app
