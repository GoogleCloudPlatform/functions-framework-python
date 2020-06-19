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

import os.path
import typing


class TestClass:
    pass


def function(request):
    # Ensure that the module for any object in this file is set correctly
    _, filename = os.path.split(__file__)
    name, _ = os.path.splitext(filename)
    assert TestClass.__mro__[0].__module__ == name

    # Ensure that calling `get_type_hints` on an object in this file succeeds
    assert typing.get_type_hints(TestClass) == {}

    return "OK"
