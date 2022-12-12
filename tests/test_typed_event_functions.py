# Copyright 2022 Google LLC
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
from functions_framework.exceptions import FunctionsFrameworkException

TEST_FUNCTIONS_DIR = pathlib.Path(__file__).resolve().parent / "test_functions"

# Python 3.5: ModuleNotFoundError does not exist
try:
    _ModuleNotFoundError = ModuleNotFoundError
except:
    _ModuleNotFoundError = ImportError


@pytest.fixture
def typed_decorator_client(function_name):
    source = TEST_FUNCTIONS_DIR / "typed_events" / "typed_event.py"
    target = function_name
    return create_app(target, source).test_client()


@pytest.fixture
def typed_decorator_missing_to_dict():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "missing_to_dict.py"
    target = "function_typed_missing_to_dict"
    return create_app(target, source).test_client()


@pytest.mark.parametrize("function_name", ["function_typed"])
def test_typed_decorator(typed_decorator_client):
    resp = typed_decorator_client.post("/", json={"name": "john", "age": 10})
    assert resp.status_code == 200
    assert resp.data == b'{"name": "john", "age": 10}'


@pytest.mark.parametrize("function_name", ["function_typed"])
def test_typed_malformed_json(typed_decorator_client):
    resp = typed_decorator_client.post("/", data="abc", content_type="application/json")
    assert resp.status_code == 500


@pytest.mark.parametrize("function_name", ["function_typed_faulty_from_dict"])
def test_typed_faulty_from_dict(typed_decorator_client):
    resp = typed_decorator_client.post(
        "/", json={"country": "Monaco", "population": 40000}
    )
    assert resp.status_code == 500


@pytest.mark.parametrize("function_name", ["function_typed_reflect"])
def test_typed_reflect_decorator(typed_decorator_client):
    resp = typed_decorator_client.post("/", json={"name": "jane", "age": 20})
    assert resp.status_code == 200
    assert resp.data == b'{"name": "jane", "age": 20}'


@pytest.mark.parametrize("function_name", ["function_typed_different_types"])
def test_typed_different_types(typed_decorator_client):
    resp = typed_decorator_client.post("/", json={"name": "jane", "age": 20})
    assert resp.status_code == 200
    assert resp.data == b'{"country": "Monaco", "population": 40000}'


@pytest.mark.parametrize("function_name", ["function_typed_no_return"])
def test_typed_no_return(typed_decorator_client):
    resp = typed_decorator_client.post("/", json={"name": "jane", "age": 20})
    assert resp.status_code == 200
    assert resp.data == b""


@pytest.mark.parametrize("function_name", ["function_typed_string_return"])
def test_typed_string_return(typed_decorator_client):
    resp = typed_decorator_client.post("/", json={"name": "jane", "age": 20})
    assert resp.status_code == 200
    assert resp.data == b"Hello jane"


def test_missing_from_dict_typed_decorator():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "missing_from_dict.py"
    target = "function_typed_missing_from_dict"
    with pytest.raises(FunctionsFrameworkException) as excinfo:
        create_app(target, source).test_client()


def test_mismatch_types_typed_decorator():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "mismatch_types.py"
    target = "function_typed_mismatch_types"
    with pytest.raises(FunctionsFrameworkException) as excinfo:
        create_app(target, source).test_client()


def test_missing_type_information_typed_decorator():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "missing_type.py"
    target = "function_typed_missing_type_information"
    with pytest.raises(FunctionsFrameworkException):
        create_app(target, source).test_client()


def test_missing_parameter_typed_decorator():
    source = TEST_FUNCTIONS_DIR / "typed_events" / "missing_parameter.py"
    target = "function_typed_missing_parameter"
    with pytest.raises(FunctionsFrameworkException):
        create_app(target, source).test_client()


def test_missing_to_dict_typed_decorator(typed_decorator_missing_to_dict):
    resp = typed_decorator_missing_to_dict.post("/", json={"name": "john", "age": 10})
    assert resp.status_code == 500
