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

from pyteal import (
    Addr,
    And,
    Balance,
    Bytes,
    Cond,
    Global,
    Gtxn,
    Int,
    Mode,
    Or,
    Substring,
    Txn,
    TxnType,
    compileTeal,
)

from algoworld_contracts.common.utils import parse_params

"""
Swapper Proxy Used for Storing Swap Configurations
1. Activate Proxy
2. Store Swap Configurations
"""

TEAL_VERSION = 6

STORE_GSIZE = Int(2)
STORE_FEE = 0
STORE_PROXY_NOTE = 1


@dataclasses.dataclass
class SwapProxy:
    swap_creator: str
    version: str


def swapper_proxy(cfg: SwapProxy):

    is_proxy_store = And(
        Global.group_size() == STORE_GSIZE,
        Gtxn[STORE_FEE].type_enum() == TxnType.Payment,
        Gtxn[STORE_PROXY_NOTE].type_enum() == TxnType.Payment,
    )

    return Cond([is_proxy_store, proxy_store(cfg)])


def proxy_store(cfg: SwapProxy):
    Balance(Txn.sender())

    store_fee = And(
        Gtxn[STORE_FEE].type_enum() == TxnType.Payment,
        Or(
            Gtxn[STORE_FEE].amount() == Int(110_000),
            Gtxn[STORE_FEE].amount() == Int(10_000),
        ),
        Gtxn[STORE_FEE].sender() == Addr(cfg.swap_creator),
        Gtxn[STORE_FEE].receiver() == Txn.sender(),
        Gtxn[STORE_FEE].rekey_to() == Global.zero_address(),
        Gtxn[STORE_FEE].close_remainder_to() == Global.zero_address(),
    )

    store_proxy_note = And(
        Gtxn[STORE_PROXY_NOTE].type_enum() == TxnType.Payment,
        Gtxn[STORE_PROXY_NOTE].amount() == Int(0),
        Gtxn[STORE_PROXY_NOTE].sender() == Txn.sender(),
        Gtxn[STORE_PROXY_NOTE].receiver() == Txn.sender(),
        Gtxn[STORE_PROXY_NOTE].rekey_to() == Global.zero_address(),
        Gtxn[STORE_PROXY_NOTE].close_remainder_to() == Global.zero_address(),
        Substring(Gtxn[STORE_PROXY_NOTE].note(), Int(0), Int(7)) == Bytes("ipfs://"),
    )

    return And(store_fee, store_proxy_note)


def compile_stateless(program):
    return compileTeal(program, Mode.Signature, version=TEAL_VERSION)


if __name__ == "__main__":
    params = {
        "swap_creator": "2ILRL5YU3FZ4JDQZQVXEZUYKEWF7IEIGRRCPCMI36VKSGDMAS6FHSBXZDQ",
        "version": "0.0.1",
    }

    # Overwrite params if sys.argv[1] is passed
    if len(sys.argv) > 1:
        params = parse_params(sys.argv[1], params)

    print(compile_stateless(swapper_proxy(SwapProxy(**params))))
