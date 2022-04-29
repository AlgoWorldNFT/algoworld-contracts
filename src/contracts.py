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

from src.auction.clear import clear
from src.auction.escrow import escrow
from src.auction.manager import manager
from src.auction.proxy import proxy

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
