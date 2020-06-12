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
import io

import flask
import json
from cloudevents.sdk import marshaller
from cloudevents.sdk.event import v1

def function(event):
    """Test HTTP function whose behavior depends on the given mode.

  The function returns a success, a failure, or throws an exception, depending
  on the given mode.

  Args:
    event: A Cloud event as defined by https://github.com/cloudevents/sdk-python.

  Returns:
    Value and status code defined for the given mode.

  """

    # todo(joelgerard): Should probably check some of this as well. 
    if (event.EventID() == "my-id"):
        return 200
    else:
        return 500
