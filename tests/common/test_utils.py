# Original file: https://github.com/scale-it/algorand-builder/blob/master/examples/algobpy/parse.py
from pytest import raises

from algoworld_contracts.common.utils import parse_params


def test_parse_args():
    dummy_input = '{"proxy_id": 1, "owner_address": "123"}'
    dummy_initial_params = {"proxy_id": 0, "owner_address": "000"}

    new_params = parse_params(dummy_input, dummy_initial_params)

    assert new_params["proxy_id"] == 1
    assert new_params["owner_address"] == "123"

    with raises(Exception):
        parse_params("[]][[]", dummy_initial_params)
