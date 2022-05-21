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
    Assert,
    Bytes,
    Global,
    Gtxn,
    Int,
    Mode,
    Return,
    Seq,
    Substring,
    Txn,
    TxnType,
    compileTeal,
)

from src.common.utils import parse_params

"""
ASA to ASA Atomic Swapper
1. Offered ASA Opt-In
2. Offered ASA / Required ASA Swap
3. Close Swap
"""

TEAL_VERSION = 6

FEE_NOTE = 0
PROXY_NOTE = 1


@dataclasses.dataclass
class SwapProxy:
    swap_creator: str


def swapper_proxy(cfg: SwapProxy):

    fee_tx = [
        Assert(Gtxn[FEE_NOTE].type_enum() == TxnType.Payment),
        Assert(Gtxn[FEE_NOTE].amount() == Int(110_000)),
        Assert(Gtxn[FEE_NOTE].sender() == Addr(cfg.swap_creator)),
        Assert(Gtxn[FEE_NOTE].receiver() == Txn.sender()),
        Assert(Gtxn[FEE_NOTE].rekey_to() == Global.zero_address()),
        Assert(Gtxn[FEE_NOTE].close_remainder_to() == Global.zero_address()),
    ]

    proxy_tx = [
        Assert(Gtxn[PROXY_NOTE].type_enum() == TxnType.Payment),
        Assert(Gtxn[PROXY_NOTE].amount() == Int(0)),
        Assert(Gtxn[PROXY_NOTE].sender() == Txn.sender()),
        Assert(Gtxn[PROXY_NOTE].receiver() == Txn.sender()),
        Assert(Gtxn[PROXY_NOTE].rekey_to() == Global.zero_address()),
        Assert(Gtxn[PROXY_NOTE].close_remainder_to() == Global.zero_address()),
        Assert(Substring(Gtxn[PROXY_NOTE].note(), Int(0), Int(4)) == Bytes("aws_")),
    ]

    finalSeq = [Assert(Global.group_size() == Int(2))]
    finalSeq.extend(fee_tx)
    finalSeq.extend(proxy_tx)
    finalSeq.append(Return(Int(1)))

    return Seq(finalSeq)


def compile_stateless(program):
    return compileTeal(program, Mode.Signature, version=TEAL_VERSION)


if __name__ == "__main__":
    params = {
        "swap_creator": "2ILRL5YU3FZ4JDQZQVXEZUYKEWF7IEIGRRCPCMI36VKSGDMAS6FHSBXZDQ",
    }

    # Overwrite params if sys.argv[1] is passed
    if len(sys.argv) > 1:
        params = parse_params(sys.argv[1], params)

    print(compile_stateless(swapper_proxy(SwapProxy(**params))))
