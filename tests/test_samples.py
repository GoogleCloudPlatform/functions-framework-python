import pathlib
import sys
import time

import docker
import pytest
import requests

EXAMPLES_DIR = pathlib.Path(__file__).resolve().parent.parent / "examples"


@pytest.mark.skipif(
    sys.platform != "linux", reason="docker only works on linux in GH actions"
)
class TestSamples:
    def stop_all_containers(self, docker_client):
        containers = docker_client.containers.list()
        for container in containers:
            container.stop()

    @pytest.mark.slow_integration_test
    def test_cloud_run_http(self):
        client = docker.from_env()
        self.stop_all_containers(client)

        TAG = "cloud_run_http"
        client.images.build(path=str(EXAMPLES_DIR / "cloud_run_http"), tag=TAG)
        container = client.containers.run(image=TAG, detach=True, ports={8080: 8080})
        timeout = 10
        success = False
        while success == False and timeout > 0:
            try:
                response = requests.get("http://localhost:8080")
                if response.text == "Hello world!":
                    success = True
            except:
                pass

            time.sleep(1)
            timeout -= 1

        container.stop()

        assert success
