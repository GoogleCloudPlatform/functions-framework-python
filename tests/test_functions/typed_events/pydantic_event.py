from __future__ import annotations

import functions_framework
from pydantic import BaseModel


class TestType(BaseModel):
    name: str
    age: int


@functions_framework.typed
def function_typed_pydantic(testType: TestType):
    valid_event = testType.name == "jane" and testType.age == 20
    if not valid_event:
        raise Exception("Received invalid input")
    return testType.model_dump()


