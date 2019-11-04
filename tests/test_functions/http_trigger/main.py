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

"""Function used in Worker tests of handling HTTP functions."""

import flask


def function(request):
    """Test HTTP function whose behavior depends on the given mode.

  The function returns a success, a failure, or throws an exception, depending
  on the given mode.

  Args:
    request: The HTTP request which triggered this function. Must contain name
      of the requested mode in the 'mode' field in JSON document in request
      body.

  Returns:
    Value and status code defined for the given mode.

  Raises:
    Exception: Thrown when requested in the incoming mode specification.
  """
    mode = request.get_json().get("mode")
    print("Mode: " + mode)  # pylint: disable=superfluous-parens
    if mode == "SUCCESS":
        return "success", 200
    elif mode == "FAILURE":
        return flask.abort(flask.Response("failure", 400))
    elif mode == "THROW":
        raise Exception("omg")
    else:
        return "invalid request", 400
