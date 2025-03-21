# Development

Quickstart for functions-framework maintainers.

## Environment setup

Install [tox](https://pypi.org/p/tox), the test runner:

```
$ python -m pip install -U tox
```

## Running linting

Linting can be run with:

```
$ python -m tox -e lint
```

## Running tests

All tests can be run with:

```
$ python -m tox
```

Tests for the current Python version can be run with:

```
$ python -m tox -e py
```

Tests for a specific Python version can be run with:

```
$ python -m tox -e py3.12
```

A specific test file (e.g. `tests/test_cli.py`) can be run with:

```
$ python -m tox -e py -- tests/test_cli.py
```

A specific test in the file (e.g. `test_cli_no_arguements` in `tests/test_cli.py`) can be run with:

```
$ python -m tox -e py -- tests/test_cli.py::test_cli_no_arguments
```

## Releasing

Releases are triggered via the [Release Please](https://github.com/apps/release-please) app, which in turn kicks off the [Release to PyPI](https://github.com/GoogleCloudPlatform/functions-framework-python/blob/main/.github/workflows/release.yml) workflow.
