# Copyright 2022 Google LLC
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
from functions_framework.exceptions import FunctionsFrameworkException

"""Registers user function in the REGISTRY_MAP and the INPUT_TYPE_MAP.
Also performs some validity checks for the input type of the function

Args:
    decorator_type: The type provided by the @typed(input_type) decorator
    func: User function
"""


def register_typed_event(decorator_type, func):
    try:
        sig = signature(func)
        annotation_type = list(sig.parameters.values())[0].annotation
        input_type = _select_input_type(decorator_type, annotation_type)
        _validate_input_type(input_type)
    except IndexError:
        raise FunctionsFrameworkException(
            "Function signature is missing an input parameter."
            "The function should be defined as 'def your_fn(in: inputType)'"
        )
    except Exception as e:
        raise FunctionsFrameworkException(
            "Functions using the @typed decorator must provide "
            "the type of the input parameter by specifying @typed(inputType) and/or using python "
            "type annotations 'def your_fn(in: inputType)'"
        )

    _function_registry.INPUT_TYPE_MAP[func.__name__] = input_type
    _function_registry.REGISTRY_MAP[
        func.__name__
    ] = _function_registry.TYPED_SIGNATURE_TYPE


""" Checks whether the response type of the typed function has a to_dict method"""


def _validate_return_type(response):
    if not (hasattr(response, "to_dict") and callable(getattr(response, "to_dict"))):
        raise AttributeError(
            "The type {response} does not have the required method called "
            " 'to_dict'.".format(response=type(response))
        )


"""Selects the input type for the typed function provided through the @typed(input_type)
decorator or through the parameter annotation in the user function
"""


def _select_input_type(decorator_type, annotation_type):
    if decorator_type == None and annotation_type is inspect._empty:
        raise TypeError(
            "The function defined does not contain Type of the input object."
        )

    if (
        decorator_type != None
        and annotation_type is not inspect._empty
        and decorator_type != annotation_type
    ):
        raise TypeError(
            "The object type provided via 'typed' decorator: '{decorator_type}'"
            "is different than the one specified by the function parameter's type annotation : '{annotation_type}'.".format(
                decorator_type=decorator_type, annotation_type=annotation_type
            )
        )

    if decorator_type == None:
        return annotation_type
    return decorator_type


"""Checks for the from_dict method implementation in the input type class"""


def _validate_input_type(input_type):
    if not (
        hasattr(input_type, "from_dict") and callable(getattr(input_type, "from_dict"))
    ):
        raise AttributeError(
            "The type {decorator_type} does not have the required method called "
            " 'from_dict'.".format(decorator_type=input_type)
        )
