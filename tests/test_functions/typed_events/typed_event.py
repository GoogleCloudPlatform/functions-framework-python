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

"""Function used to test handling functions using typed decorators."""
from typing import Any, Type, TypeVar, cast

import flask

import functions_framework

T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class TestType:
    name: str
    age: int

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age

    @staticmethod
    def from_dict(obj: dict) -> "TestType":
        name = from_str(obj.get("name"))
        age = from_int(obj.get("age"))
        return TestType(name, age)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        result["age"] = from_int(self.age)
        return result


@functions_framework.typednew(TestType)
def function_typed(testType: TestType):
    valid_event = testType.name == "john" and testType.age == 10
    if not valid_event:
        flask.abort(500)
    return testType
