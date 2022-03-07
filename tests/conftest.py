
import pytest
import requests
from urllib3.util.retry import Retry
from time import sleep
from requests.adapters import HTTPAdapter
from tests.models import AlgorandSandbox

@pytest.fixture(scope="session", autouse=True)
def algorand_sandbox(session_scoped_container_getter):
    """Wait for the api from elasticsearch to become responsive"""
    print("Waiting for algorand sandbox...")
    request_session = requests.Session()
    retries = Retry(total=20,
                    backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])
    request_session.mount('http://', HTTPAdapter(max_retries=retries))

    algod = session_scoped_container_getter.get("algod")
    algod_network = algod.network_info[0]
    algod_api_url = f'http://{algod_network.hostname}:{algod_network.host_port}/health'
    assert request_session.get(algod_api_url)

    indexer = session_scoped_container_getter.get("indexer")
    indexer_network = indexer.network_info[0]
    indexer_api_url = f'http://{indexer_network.hostname}:{indexer_network.host_port}/health'
    assert request_session.get(indexer_api_url)

    sleep(10) # TODO : find ways to await for postgresql

    return AlgorandSandbox(algod.name, indexer.name, algod_api_url, indexer_api_url)
