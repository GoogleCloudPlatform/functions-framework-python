import pathlib
import sys
import time

import docker
import pytest
import requests

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
TAG = "py_ff_conformance_tests"

@pytest.mark.skipif(
    sys.platform != "linux", reason="docker only works on linux in GH actions"
)
class TestConformance:

    @classmethod
    def setup_class(cls):
        docker.from_env().images.build(path=str(ROOT_DIR), tag={TAG}, dockerfile="conformance_runner/Dockerfile")

    def stop_all_containers(self):
        client = docker.from_env()
        containers = client.containers.list()
        for container in containers:
            container.stop()

    def setup_method(self, method):
        self.stop_all_containers()

    def run_test(self, source, signature_type, test_type):
        client = docker.from_env()
        return client.containers.run(image=TAG, environment={"signature" : signature_type, "source" : source, "test_type" : test_type})

    @pytest.mark.slow_integration_test
    def test_cloud_event(self):
        output = self.run_test("tests/conformance_tests/cloud_event_test.py","cloudevent", "cloudevent")
        assert "Validation failure" in str(output)

    @pytest.mark.slow_integration_test
    def test_legacy_event(self):
        output = self.run_test("tests/conformance_tests/legacy_event_test.py","event", "legacyevent")
        assert "Validation failure" in str(output)
