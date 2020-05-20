import pathlib
import sys

import pretend

from functions_framework import create_app

TEST_FUNCTIONS_DIR = pathlib.Path.cwd() / "tests" / "test_functions"


def test_debugger_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "googleclouddebugger", None)

    source = TEST_FUNCTIONS_DIR / "http_trigger" / "main.py"
    target = "function"

    create_app(target, source)


def test_debugger_present(monkeypatch):
    googleclouddebugger = pretend.stub(
        enable=pretend.call_recorder(lambda *a, **kw: None)
    )
    monkeypatch.setitem(sys.modules, "googleclouddebugger", googleclouddebugger)

    source = TEST_FUNCTIONS_DIR / "http_trigger" / "main.py"
    target = "function"

    create_app(target, source)

    assert googleclouddebugger.enable.calls == [
        pretend.call(module="[MODULE]", version="[VERSION]"),
    ]
