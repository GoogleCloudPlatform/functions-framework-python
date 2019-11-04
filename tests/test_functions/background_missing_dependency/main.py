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

"""Function used in Worker tests of detecting missing dependency."""
import nonexistentpackage


def function(event, context):
    """Test function which uses a package which has not been provided.

  The packaged imported above does not exist. Therefore, this import should
  fail, the Worker should detect this error, and return appropriate load
  response.

  Args:
    event: The event data which triggered this background function.
    context (google.cloud.functions.Context): The Cloud Functions event context.
  """
    del event
    del context
    nonexistentpackage.wontwork("This function isn't expected to work.")
