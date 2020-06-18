import pytest
import os
import sh
import time
import docker


@pytest.mark.slow_integration_test
def test_cloud_run_http():
    client = docker.from_env()

    cwd = os.getcwd()
    os.chdir(cwd + "/../examples/cloud_run_http")
    TAG = "cloud_run_http"
    sh.docker(["build", "--no-cache", "--tag=%s" % TAG, "."])
    cmd = sh.docker(["run", "-p:8080:8080", "-d", TAG])
    id = cmd.stdout.decode("utf-8")

    container_up = False
    timeout = 10
    while not container_up:
        output = sh.docker(["ps", "-f id=%s" % id, "-f status=running", "-q"]).stdout.decode("utf-8")
        container_up = output != ""
        time.sleep(1)
        timeout -= 1
        if timeout == 0:
          assert 0

    sample_output = sh.curl("http://localhost:8080")
    assert sample_output == "Hello world!"

    sh.docker(["stop", id])

