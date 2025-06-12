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

import uvicorn


class StarletteApplication:
    """A Starlette application that uses Uvicorn for direct serving (development mode)."""

    def __init__(self, app, host, port, debug, **options):
        """Initialize the Starlette application.

        Args:
            app: The ASGI application to serve
            host: The host to bind to
            port: The port to bind to
            debug: Whether to run in debug mode
            **options: Additional options to pass to Uvicorn
        """
        self.app = app
        self.host = host
        self.port = port
        self.debug = debug

        self.options = {
            "log_level": "debug" if debug else "error",
        }
        self.options.update(options)

    def run(self):
        """Run the Uvicorn server directly."""
        uvicorn.run(self.app, host=self.host, port=int(self.port), **self.options)
