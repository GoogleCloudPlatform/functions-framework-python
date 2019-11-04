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

"""Functions used in Worker tests of handling multiple entry points."""


def fun(name, event):
    """Test function implementation.

  It writes the expected output (entry point name and the given value) to the
  given file, as a response from the background function, verified by the test.

  Args:
    name: Entry point function which called this helper function.
    event: The event which triggered this background function. Must contain
      entries for 'value' and 'filename' keys in the data dictionary.
  """
    filename = event["filename"]
    value = event["value"]
    f = open(filename, "w")
    f.write('{{"entryPoint": "{}", "value": "{}"}}'.format(name, value))
    f.close()


def myFunctionFoo(
    event, context
):  # Used in test, pylint: disable=invalid-name,unused-argument
    """Test function at entry point myFunctionFoo.

  Loaded in a test which verifies entry point handling in a file with multiple
  entry points.

  Args:
    event: The event data (as dictionary) which triggered this background
      function. Must contain entries for 'value' and 'filename' keys in the data
      dictionary.
    context (google.cloud.functions.Context): The Cloud Functions event context.
  """
    fun("myFunctionFoo", event)


def myFunctionBar(
    event, context
):  # Used in test, pylint: disable=invalid-name,unused-argument
    """Test function at entry point myFunctionBar.

  Loaded in a test which verifies entry point handling in a file with multiple
  entry points.

  Args:
    event: The event data (as dictionary) which triggered this background
      function. Must contain entries for 'value' and 'filename' keys in the data
      dictionary.
    context (google.cloud.functions.Context): The Cloud Functions event context.
  """
    fun("myFunctionBar", event)


# Used in a test which loads an existing identifier which is not a function.
notAFunction = 42  # Used in test, pylint: disable=invalid-name
