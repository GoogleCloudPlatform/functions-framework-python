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
from cloudevents.sdk import converters
from cloudevents.sdk import marshaller
from cloudevents.sdk.converters import structured

def hello(cloudevent):
    m = marshaller.NewHTTPMarshaller([structured.NewJSONHTTPCloudEventConverter()])
    headers, body = m.ToRequest(cloudevent, converters.TypeStructured, lambda x: x)
    text_file = open("function_output.json", "w")
    text_file.write(body.getvalue().decode("utf-8"))
    text_file.close()
