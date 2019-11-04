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

"""Function used in Worker tests of HTTP request contents."""


def function(request):
    """Test function which returns the requested element of the HTTP request.

  Name of the requested HTTP request element is provided in the 'mode' field in
  the incoming JSON document.

  Args:
    request: The HTTP request which triggered this function. Must contain name
      of the requested HTTP request element in the 'mode' field in JSON document
      in request body.

  Returns:
    Value of the requested HTTP request element, or 'Bad Request' status in case
    of unrecognized incoming request.
  """
    mode = request.get_json().get("mode")
    if mode == "path":
        return request.path
    elif mode == "url":
        return request.url
    else:
        return "invalid request", 400
