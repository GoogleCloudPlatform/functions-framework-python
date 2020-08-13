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

"""Function used in Worker tests of detecting load failure."""


def function(event, context):
  """Test function with a syntax error.

  The Worker is expected to detect this error when loading the function, and
  return appropriate load response.

  Args:
    event: The event data which triggered this background function.
    context (google.cloud.functions.Context): The Cloud Functions event context.
  """
  # Syntax error: an extra closing parenthesis in the line below.
  print('foo'))
