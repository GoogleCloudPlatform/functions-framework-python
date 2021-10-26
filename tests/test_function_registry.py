# Copyright 2021 Google LLC
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

from functions_framework import _function_registry


def test_get_function_signature():
    test_cases = [
        {
            "name": "get decorator type",
            "function": "my_func",
            "registered_type": "http",
            "flag_type": "event",
            "env_type": "event",
            "want_type": "http",
        },
        {
            "name": "get flag type",
            "function": "my_func_1",
            "registered_type": "",
            "flag_type": "event",
            "env_type": "http",
            "want_type": "event",
        },
        {
            "name": "get env var",
            "function": "my_func_2",
            "registered_type": "",
            "flag_type": "",
            "env_type": "event",
            "want_type": "event",
        },
    ]
    for case in test_cases:
        _function_registry.REGISTRY_MAP[case["function"]] = case["registered_type"]
        os.environ[_function_registry.FUNCTION_SIGNATURE_TYPE] = case["env_type"]
        signature_type = _function_registry.get_func_signature_type(
            case["function"], case["flag_type"]
        )

        assert signature_type == case["want_type"], case["name"]


def test_get_function_signature_default():
    _function_registry.REGISTRY_MAP["my_func"] = ""
    if _function_registry.FUNCTION_SIGNATURE_TYPE in os.environ:
        del os.environ[_function_registry.FUNCTION_SIGNATURE_TYPE]
    signature_type = _function_registry.get_func_signature_type("my_func", None)

    assert signature_type == "http"
