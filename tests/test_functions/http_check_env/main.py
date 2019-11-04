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

"""Function used in Worker tests of environment variables setup."""
import os

X_GOOGLE_FUNCTION_NAME = "gcf-function"
X_GOOGLE_ENTRY_POINT = "function"
HOME = "/tmp"


def function(request):
    """Test function which returns the requested environment variable value.

  Args:
    request: The HTTP request which triggered this function. Must contain name
      of the requested environment variable in the 'mode' field in JSON document
      in request body.

  Returns:
    Value of the requested environment variable.
  """
    name = request.get_json().get("mode")
    return os.environ[name]
