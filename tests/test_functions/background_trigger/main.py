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

"""Function used in Worker tests of handling background functions."""


def function(
    event, context
):  # Required by function definition pylint: disable=unused-argument
    """Test background function.

  It writes the expected output (entry point name and the given value) to the
  given file, as a response from the background function, verified by the test.

  Args:
    event: The event data (as dictionary) which triggered this background
      function. Must contain entries for 'value' and 'filename' keys in the
      data dictionary.
    context (google.cloud.functions.Context): The Cloud Functions event context.
  """
    filename = event["filename"]
    value = event["value"]
    f = open(filename, "w")
    f.write('{{"entryPoint": "function", "value": "{}"}}'.format(value))
    f.close()
