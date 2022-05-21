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

import dataclasses
import sys

from pyteal import Addr, And, Cond, Global, Gtxn, Int, Mode, TxnType, compileTeal

from algoworld_contracts.common.utils import parse_params

"""
ASA to ASA Atomic Swapper
1. Offered ASA Opt-In
2. Offered ASA / Required ASA Swap
3. Close Swap
"""

TEAL_VERSION = 6

MAX_FEE = Int(1000)
OPTIN_FUNDING_AMOUNT = 210000

ASA_OPTIN_GSIZE = Int(2)
OPTIN_FEE = 0
ASA_OPTIN = 1

ASA_SWAP_GSIZE = Int(3)
OFFERED_ASA_XFER = 0
REQUESTED_ASA_XFER = 1
INCENTIVE_FEE = 2

CLOSE_SWAP_GSIZE = Int(3)
ASA_CLOSE = 0
SWAP_CLOSE = 1
PROOF = 2


@dataclasses.dataclass
class AsaToAsaSwapConfig:
    swap_creator: str
    offered_asa_id: int
    offered_asa_amount: int
    requested_asa_id: int
    requested_asa_amount: int
    incentive_fee_address: str
    incentive_fee_amount: int


def swapper(cfg: AsaToAsaSwapConfig):

    is_asa_optin = And(
        Global.group_size() == ASA_OPTIN_GSIZE,
        Gtxn[OPTIN_FEE].type_enum() == TxnType.Payment,
        Gtxn[ASA_OPTIN].type_enum() == TxnType.AssetTransfer,
    )

    is_asa_swap = And(
        Global.group_size() == ASA_SWAP_GSIZE,
        Gtxn[OFFERED_ASA_XFER].type_enum() == TxnType.AssetTransfer,
        Gtxn[REQUESTED_ASA_XFER].type_enum() == TxnType.AssetTransfer,
        Gtxn[INCENTIVE_FEE].type_enum() == TxnType.Payment,
    )

    is_close_swap = And(
        Global.group_size() == CLOSE_SWAP_GSIZE,
        Gtxn[ASA_CLOSE].type_enum() == TxnType.AssetTransfer,
        Gtxn[SWAP_CLOSE].type_enum() == TxnType.Payment,
        Gtxn[PROOF].type_enum() == TxnType.Payment,
    )

    return Cond(
        [is_asa_optin, asa_optin(cfg)],
        [is_asa_swap, asa_swap(cfg)],
        [is_close_swap, close_swap(cfg)],
    )


def asa_optin(cfg: AsaToAsaSwapConfig):

    optin_fee_precondition = And(
        Gtxn[OPTIN_FEE].fee() <= MAX_FEE,
        Gtxn[OPTIN_FEE].rekey_to() == Global.zero_address(),
        Gtxn[OPTIN_FEE].close_remainder_to() == Global.zero_address(),
    )

    asa_optin_precondition = And(
        Gtxn[ASA_OPTIN].fee() <= MAX_FEE,
        Gtxn[ASA_OPTIN].rekey_to() == Global.zero_address(),
        Gtxn[ASA_OPTIN].asset_sender() == Global.zero_address(),
        Gtxn[ASA_OPTIN].asset_close_to() == Global.zero_address(),
    )

    return And(
        optin_fee_precondition,
        asa_optin_precondition,
        Gtxn[OPTIN_FEE].sender() == Addr(cfg.swap_creator),
        Gtxn[OPTIN_FEE].receiver() == Gtxn[ASA_OPTIN].sender(),
        Gtxn[OPTIN_FEE].amount() >= Int(OPTIN_FUNDING_AMOUNT),
        Gtxn[ASA_OPTIN].xfer_asset() == Int(cfg.offered_asa_id),
        Gtxn[ASA_OPTIN].sender() == Gtxn[ASA_OPTIN].asset_receiver(),
        Gtxn[ASA_OPTIN].asset_amount() == Int(0),
    )


def asa_swap(cfg: AsaToAsaSwapConfig):

    offered_asa_xfer_precondition = And(
        Gtxn[OFFERED_ASA_XFER].fee() <= MAX_FEE,
        Gtxn[OFFERED_ASA_XFER].rekey_to() == Global.zero_address(),
        Gtxn[OFFERED_ASA_XFER].asset_sender() == Global.zero_address(),
        Gtxn[OFFERED_ASA_XFER].asset_close_to() == Global.zero_address(),
    )

    requested_asa_xfer_precondition = And(
        Gtxn[REQUESTED_ASA_XFER].asset_sender() == Global.zero_address()
    )

    return And(
        offered_asa_xfer_precondition,
        requested_asa_xfer_precondition,
        Gtxn[OFFERED_ASA_XFER].xfer_asset() == Int(cfg.offered_asa_id),
        Gtxn[OFFERED_ASA_XFER].asset_amount() == Int(cfg.offered_asa_amount),
        Gtxn[REQUESTED_ASA_XFER].xfer_asset() == Int(cfg.requested_asa_id),
        Gtxn[REQUESTED_ASA_XFER].asset_amount() == Int(cfg.requested_asa_amount),
        Gtxn[OFFERED_ASA_XFER].asset_receiver() == Gtxn[REQUESTED_ASA_XFER].sender(),
        Gtxn[REQUESTED_ASA_XFER].asset_receiver() == Addr(cfg.swap_creator),
        Gtxn[INCENTIVE_FEE].receiver() == Addr(cfg.incentive_fee_address),
        Gtxn[INCENTIVE_FEE].sender() == Gtxn[REQUESTED_ASA_XFER].sender(),
        Gtxn[INCENTIVE_FEE].amount() == Int(cfg.incentive_fee_amount),
    )


def close_swap(cfg: AsaToAsaSwapConfig):

    asa_close_precondition = And(
        Gtxn[ASA_CLOSE].fee() <= MAX_FEE,
        Gtxn[ASA_CLOSE].rekey_to() == Global.zero_address(),
        Gtxn[ASA_CLOSE].asset_sender() == Global.zero_address(),
    )

    swap_close_precondition = And(
        Gtxn[SWAP_CLOSE].fee() <= MAX_FEE,
        Gtxn[SWAP_CLOSE].rekey_to() == Global.zero_address(),
    )

    return And(
        asa_close_precondition,
        swap_close_precondition,
        Gtxn[ASA_CLOSE].xfer_asset() == Int(cfg.offered_asa_id),
        Gtxn[ASA_CLOSE].asset_receiver() == Addr(cfg.swap_creator),
        Gtxn[ASA_CLOSE].asset_close_to() == Addr(cfg.swap_creator),
        Gtxn[SWAP_CLOSE].receiver() == Addr(cfg.swap_creator),
        Gtxn[SWAP_CLOSE].close_remainder_to() == Addr(cfg.swap_creator),
        Gtxn[PROOF].sender() == Addr(cfg.swap_creator),
        Gtxn[PROOF].receiver() == Addr(cfg.swap_creator),
        Gtxn[PROOF].amount() == Int(0),
    )


def compile_stateless(program):
    return compileTeal(program, Mode.Signature, version=TEAL_VERSION)


if __name__ == "__main__":
    params = {
        "swap_creator": "2ILRL5YU3FZ4JDQZQVXEZUYKEWF7IEIGRRCPCMI36VKSGDMAS6FHSBXZDQ",
        "offered_asa_id": 42,
        "offered_asa_amount": 1,
        "requested_asa_id": 69,
        "requested_asa_amount": 1,
        "incentive_fee_address": "RJVRGSPGSPOG7W3V7IMZZ2BAYCABW3YC5MWGKEOPAEEI5ZK5J2GSF6Y26A",
        "incentive_fee_amount": 10_000,
    }

    # Overwrite params if sys.argv[1] is passed
    if len(sys.argv) > 1:
        params = parse_params(sys.argv[1], params)

    print(compile_stateless(swapper(AsaToAsaSwapConfig(**params))))
