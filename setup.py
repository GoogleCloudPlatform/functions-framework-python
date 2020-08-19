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

from io import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="functions-framework",
    version="1.6.0",
    description="An open source FaaS (Function as a service) framework for writing portable Python functions -- brought to you by the Google Cloud Functions team.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/googlecloudplatform/functions-framework-python",
    author="Google LLC",
    author_email="googleapis-packages@google.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="functions-framework",
    packages=find_packages(where="src"),
    namespace_packages=["google", "google.cloud"],
    package_dir={"": "src"},
    python_requires=">=3.5, <4",
    install_requires=[
        "flask>=1.0,<2.0",
        "click>=7.0,<8.0",
        "watchdog>=0.10.0",
        "gunicorn>=19.2.0,<21.0; platform_system!='Windows'",
    ],
    entry_points={
        "console_scripts": [
            "functions-framework=functions_framework._cli:_cli",
            "functions_framework=functions_framework._cli:_cli",
            "ff=functions_framework._cli:_cli",
        ]
    },
)
