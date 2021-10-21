import pathlib
import sys
import time

import docker
import pytest
import requests

from cloudevents.http import CloudEvent, to_structured

EXAMPLES_DIR = pathlib.Path(__file__).resolve().parent.parent / "examples"


@pytest.mark.skipif(
    sys.platform != "linux", reason="docker only works on linux in GH actions"
)
@pytest.fixture
def cloudevent_1_0():
    attributes = {
        "specversion": "1.0",
        "id": "my-id",
        "source": "from-galaxy-far-far-away",
        "type": "cloudevent.greet.you",
        "time": "2020-08-16T13:58:54.471765",
    }
    data = {"name": "john"}
    return CloudEvent(attributes, data)


class TestSamples:
    def stop_all_containers(self, docker_client):
        containers = docker_client.containers.list()
        for container in containers:
            container.stop()

    # @pytest.mark.slow_integration_test
    # def test_cloud_run_http(self):
    #     client = docker.from_env()
    #     self.stop_all_containers(client)
    #
    #     TAG = "cloud_run_http"
    #     client.images.build(path=str(EXAMPLES_DIR / "cloud_run_http"), tag={TAG})
    #     container = client.containers.run(image=TAG, detach=True, ports={8080: 8080})
    #     timeout = 10
    #     success = False
    #     while success == False and timeout > 0:
    #         try:
    #             response = requests.get("http://localhost:8080")
    #             if response.text == "Hello world!":
    #                 success = True
    #         except:
    #             pass
    #
    #         time.sleep(1)
    #         timeout -= 1
    #
    #     container.stop()
    #
    #     assert success

    @pytest.mark.slow_integration_test
    def test_cloud_run_decorator(self):
        client = docker.from_env()
        self.stop_all_containers(client)

        TAG = "cloud_run_decorator"
        client.images.build(path=str(EXAMPLES_DIR / "cloud_run_decorator"), tag={TAG})
        container = client.containers.run(image=TAG, detach=True, ports={8080: 8080})
        timeout = 10
        success = False
        while not success and timeout > 0:
            try:
                headers, data = to_structured(cloudevent_1_0)
                response = requests.post(
                    "http://localhost:8080/", headers=headers, data=data
                )

                print(response.text)
                if "Received" in response.text:
                    success = True
            except:
                pass

            time.sleep(1)
            timeout -= 1

        container.stop()

        assert success
