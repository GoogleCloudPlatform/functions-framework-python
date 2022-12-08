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

import flask

import functions_framework


class TestType1:
    name: str
    age: int

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age


class TestType2:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


@functions_framework.typed(TestType2)
def function_typed_mismatch_types(test_type: TestType1):
    valid_event = test_type.name == "john" and test_type.age == 10
    if not valid_event:
        raise Exception("Received invalid input")
    return test_type
