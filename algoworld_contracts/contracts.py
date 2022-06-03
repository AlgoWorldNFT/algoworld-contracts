"""
MIT License

Copyright (c) 2022 AlgoWorld

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from pyteal import Mode, compileTeal

from algoworld_contracts.auction.clear import clear
from algoworld_contracts.auction.escrow import escrow
from algoworld_contracts.auction.manager import manager
from algoworld_contracts.auction.proxy import proxy
from algoworld_contracts.swapper.asa_to_asa_swapper import AsaToAsaSwapConfig, swapper
from algoworld_contracts.swapper.asas_to_algo_swapper import (
    AsasToAlgoSwapConfig,
    multi_asa_swapper,
)
from algoworld_contracts.swapper.swap_proxy import SwapProxy, swapper_proxy

TEAL_VERSION = 6


def get_clear_teal():
    return compileTeal(clear(), Mode.Application, version=TEAL_VERSION)


def get_escrow_teal(app_id: int, nft_id: int, fee_address_a: str, fee_address_b: str):
    return compileTeal(
        escrow(app_id, nft_id, fee_address_a, fee_address_b),
        Mode.Signature,
        version=TEAL_VERSION,
    )


def get_proxy_teal(proxy_id: int):
    return compileTeal(proxy(proxy_id), Mode.Signature, version=TEAL_VERSION)


def get_manager_teal(fee_address_a: str, fee_address_b: str, contract_version: str):
    return compileTeal(
        manager(fee_address_a, fee_address_b, contract_version),
        Mode.Application,
        version=TEAL_VERSION,
    )


def get_swapper_teal(
    swap_creator: str,
    offered_asa_id: int,
    offered_asa_amount: int,
    requested_asa_id: int,
    requested_asa_amount: int,
    incentive_fee_address: str,
    incentive_fee_amount: int,
):
    return compileTeal(
        swapper(
            AsaToAsaSwapConfig(
                swap_creator=swap_creator,
                offered_asa_id=offered_asa_id,
                offered_asa_amount=offered_asa_amount,
                requested_asa_id=requested_asa_id,
                requested_asa_amount=requested_asa_amount,
                incentive_fee_address=incentive_fee_address,
                incentive_fee_amount=incentive_fee_amount,
            )
        ),
        Mode.Signature,
        version=TEAL_VERSION,
    )


def get_swapper_proxy_teal(swap_creator: str, version: str):
    return compileTeal(
        swapper_proxy(SwapProxy(swap_creator, version)),
        Mode.Signature,
        version=TEAL_VERSION,
    )


def get_multi_swapper_teal(
    swap_creator: str,
    offered_asa_amounts: dict[int, int],
    requested_algo_amount: int,
    max_fee: int,
    optin_funding_amount: int,
    incentive_fee_address: str,
    incentive_fee_amount: int,
):
    return compileTeal(
        multi_asa_swapper(
            AsasToAlgoSwapConfig(
                swap_creator=swap_creator,
                offered_asa_amounts=offered_asa_amounts,
                requested_algo_amount=requested_algo_amount,
                max_fee=max_fee,
                optin_funding_amount=optin_funding_amount,
                incentive_fee_address=incentive_fee_address,
                incentive_fee_amount=incentive_fee_amount,
            )
        ),
        Mode.Signature,
        version=TEAL_VERSION,
    )
