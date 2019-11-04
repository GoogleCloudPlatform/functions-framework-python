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

"""Function used in Worker tests of function execution time."""
import time


def function(request):
    """Test function which sleeps for the given number of seconds.

  The test verifies that it gets the response from the function only after the
  given number of seconds.

  Args:
    request: The HTTP request which triggered this function. Must contain the
      requested number of seconds in the 'mode' field in JSON document in
      request body.
  """
    sleep_sec = int(request.get_json().get("mode")) / 1000.0
    time.sleep(sleep_sec)
    return "OK"
