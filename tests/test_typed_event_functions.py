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
import pathlib

import pytest

from functions_framework import create_app
from functions_framework.exceptions import MissingMethodException, MissingTypeException

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"

# Python 3.5: ModuleNotFoundError does not exist
try:
    _ModuleNotFoundError = ModuleNotFoundError
except:
    _ModuleNotFoundError = ImportError


@pytest.fixture
def typed_decorator_client():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "typed_event.py"
    target = "function_typed"
    return create_app(target, source).test_client()


@pytest.fixture
def typed_decorator_missing_todict():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "missing_to_dict.py"
    target = "function_typed_missing_to_dict"
    return create_app(target, source).test_client()


def test_typed_decorator(typed_decorator_client):
    resp = typed_decorator_client.post("/", json={"name": "john", "age": 10})
    assert resp.status_code == 200
    assert resp.data == b'{"age":10,"name":"john"}\n'


def test_missing_from_dict_typed_decorator():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "missing_from_dict.py"
    target = "function_typed_missing_from_dict"
    with pytest.raises(MissingMethodException) as excinfo:
        create_app(target, source).test_client()


def test_missing_type_information_typed_decorator():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "missing_type.py"
    target = "function_typed_missing_type_information"
    with pytest.raises(MissingTypeException):
        create_app(target, source).test_client()


def test_missing_to_dict_typed_decorator(typed_decorator_missing_todict):
    resp = typed_decorator_missing_todict.post("/", json={"name": "john", "age": 10})
    assert resp.status_code == 500
