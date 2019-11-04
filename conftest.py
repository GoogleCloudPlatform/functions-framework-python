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

import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate_environment():
    """Ensure any changes to the environment are isolated to individual tests"""
    _environ = os.environ.copy()
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(_environ)
