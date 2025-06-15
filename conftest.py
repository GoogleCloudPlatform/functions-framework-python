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

import logging
import os
import sys

from importlib import reload

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


@pytest.fixture(scope="function", autouse=True)
def isolate_logging():
    "Ensure any changes to logging are isolated to individual tests" ""
    try:
        yield
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        logging.shutdown()
        reload(logging)


# Safe to remove when we drop Python 3.7 support
def pytest_ignore_collect(collection_path, config):
    """Ignore async test files on Python 3.7 since Starlette requires Python 3.8+"""
    if sys.version_info >= (3, 8):
        return None

    # Skip test_aio.py, test_asgi.py, and test_execution_id_async.py entirely on Python 3.7
    if collection_path.name in [
        "test_aio.py",
        "test_asgi.py",
        "test_execution_id_async.py",
    ]:
        return True

    return None


# Safe to remove when we drop Python 3.7 support
def pytest_collection_modifyitems(config, items):
    """Skip async-related tests on Python 3.7 since Starlette requires Python 3.8+"""
    if sys.version_info >= (3, 8):
        return

    skip_async = pytest.mark.skip(
        reason="Async features require Python 3.8+ (Starlette dependency)"
    )

    # Keywords that indicate async-related tests
    async_keywords = ["async", "asgi", "aio", "starlette"]

    for item in items:
        skip_test = False

        if hasattr(item, "callspec") and hasattr(item.callspec, "params"):
            for param_name, param_value in item.callspec.params.items():
                # Check if test has fixtures with async-related parameters
                if isinstance(param_value, str) and any(
                    keyword in param_value.lower() for keyword in async_keywords
                ):
                    skip_test = True
                    break
                # Skip tests parametrized with None (create_asgi_app on Python 3.7)
                if param_value is None:
                    skip_test = True
                    break

        # Skip tests that explicitly test async functionality
        if any(keyword in item.name.lower() for keyword in async_keywords):
            skip_test = True

        if skip_test:
            item.add_marker(skip_async)
