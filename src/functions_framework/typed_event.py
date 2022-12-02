# Copyright 2021 Google LLC
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


import inspect

from inspect import signature

from functions_framework import _function_registry


class TypedEvent(object):

    # Supports v1beta1, v1beta2, and v1 event formats.
    def __init__(
        self,
        data,
    ):
        self.data = data


def register_typed_event2(decorator_type, contextSet, func):
    print("######")
    print(decorator_type)
    print(contextSet)
    sig = signature(func)
    annotation_type = list(sig.parameters.values())[0].annotation
    print(annotation_type)
    type_validity_check(decorator_type, annotation_type)
    if decorator_type == "":
        decorator_type = annotation_type

    _function_registry.INPUT_MAP[func.__name__] = decorator_type
    _function_registry.REGISTRY_MAP[
        func.__name__
    ] = _function_registry.TYPED_SIGNATURE_TYPE
    _function_registry.CONTEXT_MAP[func.__name__] = contextSet


def register_typed_event(decorator_type, func):
    sig = signature(func)
    annotation_type = list(sig.parameters.values())[0].annotation

    type_validity_check(decorator_type, annotation_type)
    if decorator_type == "":
        decorator_type = annotation_type

    _function_registry.INPUT_MAP[func.__name__] = decorator_type
    _function_registry.REGISTRY_MAP[
        func.__name__
    ] = _function_registry.TYPED_SIGNATURE_TYPE


def validate_return_type(response):
    if not (hasattr(response, "to_dict") and callable(getattr(response, "to_dict"))):
        raise AttributeError(
            "The type {response} does not have the required method called "
            " 'to_dict'.".format(response=response)
        )


def type_validity_check(decorator_type, annotation_type):
    if decorator_type == "" and annotation_type is inspect._empty:
        raise TypeError(
            "The function defined does not contain Type of the input object."
        )

    if (
        decorator_type != ""
        and annotation_type is not inspect._empty
        and decorator_type != annotation_type
    ):
        raise TypeError(
            "The object type provided via 'typed' {decorator_type}"
            "is different from the one in the function annotation {annotation_type}.".format(
                decorator_type=decorator_type, annotation_type=annotation_type
            )
        )

    if decorator_type == "":
        decorator_type = annotation_type

    if not (
        hasattr(decorator_type, "from_dict")
        and callable(getattr(decorator_type, "from_dict"))
    ):
        raise AttributeError(
            "The type {decorator_type} does not have the required method called "
            " 'from_dict'.".format(decorator_type=decorator_type)
        )
