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

import gunicorn.app.base


class GunicornApplication(gunicorn.app.base.Application):
    def __init__(self, load_app, host, port, debug, **options):
        self.options = {
            "bind": "%s:%s" % (host, port),
            "workers": 1,
            "threads": 8,
            "timeout": 0,
        }
        self.options.update(options)
        self.load_app = load_app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        # The WSGI app MUST be initalized here in order for the debugger to
        # correctly trigger breakpoints
        return self.load_app()
