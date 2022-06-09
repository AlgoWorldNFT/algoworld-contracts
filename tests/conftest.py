import subprocess
from subprocess import PIPE
from time import sleep

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tests.models import AlgorandSandbox


def run_command(command, timeout=1000):
    debugcommand = " - {0}".format(" ".join(command))
    print("Running command: {0}".format(debugcommand))

    popen = subprocess.Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    popen.wait(timeout)  # wait a little for docker to complete

    return popen


@pytest.fixture(scope="session", autouse=True)
def algorand_sandbox():
    run_command(
        ["docker-compose", "-f", "tests/sandbox/docker-compose.yaml", "down"], 2000
    )
    run_command(
        ["docker-compose", "-f", "tests/sandbox/docker-compose.yaml", "up", "-d"], 5000
    )

    """Wait for the api from elasticsearch to become responsive"""
    print("Waiting for algorand sandbox...")
    request_session = requests.Session()
    retries = Retry(total=20, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    request_session.mount("http://", HTTPAdapter(max_retries=retries))

    algod_api_url = "http://0.0.0.0:4001/health"
    assert request_session.get(algod_api_url)

    indexer_api_url = "http://0.0.0.0:8980/health"
    assert request_session.get(indexer_api_url)

    sleep(5)

    yield AlgorandSandbox("aws-algod", "aws-indexer", algod_api_url, indexer_api_url)

    sleep(5)

    run_command(["docker-compose", "-f", "tests/sandbox/docker-compose.yaml", "down"])
