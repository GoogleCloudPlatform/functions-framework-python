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


class SampleType:
    country: str
    population: int

    def __init__(self, country: str, population: int) -> None:
        self.country = country
        self.population = population

    @staticmethod
    def from_dict(obj: dict) -> "SampleType":
        country = from_str(obj.get("country"))
        population = from_int(obj.get("population"))
        return SampleType(country, population)

    def to_dict(self) -> dict:
        result: dict = {}
        result["country"] = from_str(self.country)
        result["population"] = from_int(self.population)
        return result


class FaultyType:
    country: str
    population: int

    def __init__(self, country: str, population: int) -> None:
        self.country = country
        self.population = population

    @staticmethod
    def from_dict(obj: dict) -> "SampleType":
        country = from_str(obj.get("country"))
        population = from_int(obj.get("population"))
        return SampleType(country, population / 0)


@functions_framework.typed(TestType)
def function_typed(testType: TestType):
    valid_event = testType.name == "john" and testType.age == 10
    if not valid_event:
        raise Exception("Received invalid input")
    return testType


@functions_framework.typed
def function_typed_reflect(testType: TestType):
    valid_event = testType.name == "jane" and testType.age == 20
    if not valid_event:
        raise Exception("Received invalid input")
    return testType


@functions_framework.typed
def function_typed_no_return(testType: TestType):
    valid_event = testType.name == "jane" and testType.age == 20
    if not valid_event:
        raise Exception("Received invalid input")


@functions_framework.typed
def function_typed_string_return(testType: TestType):
    valid_event = testType.name == "jane" and testType.age == 20
    if not valid_event:
        raise Exception("Received invalid input")
    return "Hello " + testType.name


@functions_framework.typed(TestType)
def function_typed_different_types(testType: TestType) -> SampleType:
    valid_event = testType.name == "jane" and testType.age == 20
    if not valid_event:
        raise Exception("Received invalid input")
    sampleType = SampleType("Monaco", 40000)
    return sampleType


@functions_framework.typed
def function_typed_faulty_from_dict(input: FaultyType):
    valid_event = input.country == "Monaco" and input.population == 40000
    if not valid_event:
        raise Exception("Received invalid input")
