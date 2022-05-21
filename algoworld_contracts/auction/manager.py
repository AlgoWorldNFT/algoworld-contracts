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

import sys

from pyteal import (
    Addr,
    And,
    App,
    Assert,
    Btoi,
    Bytes,
    Cond,
    Global,
    Gtxn,
    If,
    Int,
    Mode,
    OnComplete,
    Or,
    Return,
    ScratchSlot,
    Seq,
    TealType,
    Txn,
    TxnType,
    compileTeal,
)

from algoworld_contracts.common.utils import parse_params

if __name__ == "__main__":
    from helpers.state import GlobalState, LocalState
else:
    from .helpers.state import GlobalState, LocalState

TEAL_VERSION = 6


class ManagerContract:
    def __init__(self, fee_addr1: str, fee_addr2: str, contract_version_value: str):
        self.nft_id = GlobalState("N")
        self.escrow_address = GlobalState("E")
        self.ask_price = GlobalState("A")
        self.bids_amount = GlobalState("B")
        self.owner_address = GlobalState("O")
        self.creator_address = GlobalState("C")
        self.bid_price = LocalState("B")
        self.contract_version = GlobalState("V")
        self.fee_addr1 = fee_addr1
        self.fee_addr2 = fee_addr2
        self.contract_version_value = int(contract_version_value)

    def on_register(self):
        return Seq(
            [
                # Set default values for user
                If(
                    Global.group_size() == Int(1),
                    Seq(
                        [
                            self.bid_price.put(Int(0)),
                            Return(Int(1)),
                        ]
                    ),
                    Return(Int(0)),
                )
            ]
        )

    def on_bid(self):
        is_valid_tx = ScratchSlot()
        prev_bid = ScratchSlot()
        return Seq(
            [
                prev_bid.store(self.bid_price.get()),
                # Increase bid_price
                If(
                    Global.group_size() == Int(2),
                    Seq(
                        [
                            Assert(
                                And(
                                    Gtxn[1].receiver() == self.escrow_address.get(),
                                    Gtxn[1].sender() == Gtxn[0].sender(),
                                    Gtxn[1].type_enum() == TxnType.Payment,
                                )
                            ),
                            self.bid_price.put(self.bid_price.get() + Gtxn[1].amount()),
                            is_valid_tx.store(Int(1)),
                        ]
                    ),
                    If(
                        Global.group_size() == Int(3),
                        Seq(
                            [
                                Assert(
                                    And(
                                        Gtxn[2].sender() == self.escrow_address.get(),
                                        # Cover fee
                                        Gtxn[1].receiver() == self.escrow_address.get(),
                                        Gtxn[2].amount() != Int(0),
                                    )
                                ),
                                self.bid_price.put(
                                    self.bid_price.get() - Gtxn[2].amount(),
                                ),
                                is_valid_tx.store(Int(1)),
                            ]
                        ),
                        is_valid_tx.store(Int(0)),
                    ),
                ),
                # Decrease bid_price
                Assert(
                    is_valid_tx.load(TealType.uint64) == Int(1),
                ),
                If(
                    And(
                        self.bid_price.get() != Int(0),
                        prev_bid.load(TealType.uint64) == Int(0),
                    ),
                    Seq([self.bids_amount.put(self.bids_amount.get() + Int(1))]),
                ),
                If(
                    And(
                        self.bid_price.get() == Int(0),
                        prev_bid.load(TealType.uint64) != Int(0),
                    ),
                    Seq([self.bids_amount.put(self.bids_amount.get() - Int(1))]),
                ),
                Return(Int(1)),
            ]
        )

    def on_set_price(self):
        return Seq(
            [
                # Deposit NFT on first call of set_price
                If(
                    Global.group_size() == Int(2),
                    Seq(
                        [
                            Assert(
                                And(
                                    self.owner_address.get() == Global.zero_address(),
                                    self.ask_price.get() == Int(0),
                                    Gtxn[1].asset_receiver()
                                    == self.escrow_address.get(),
                                    Gtxn[1].type_enum() == TxnType.AssetTransfer,
                                    Gtxn[1].xfer_asset() == self.nft_id.get(),
                                    Gtxn[1].asset_amount() == Int(1),
                                    Gtxn[1].sender() == Gtxn[0].sender(),
                                )
                            ),
                            self.owner_address.put(Txn.sender()),
                        ]
                    ),
                ),
                Assert(
                    And(
                        Btoi(Txn.application_args[1]) != self.ask_price.get(),
                        self.owner_address.get() == Txn.sender(),
                    )
                ),
                self.ask_price.put(Btoi(Txn.application_args[1])),
                If(
                    Global.group_size() == Int(3),
                    Seq(
                        [
                            Assert(Gtxn[2].sender() == self.escrow_address.get()),
                            self.owner_address.put(Global.zero_address()),
                            Return(Int(1)),
                        ]
                    ),
                ),
                Assert(self.ask_price.get() != Int(0)),
                Return(Int(1)),
            ]
        )

    def on_buy_now(self):
        return Seq(
            [
                # Ensure that ask_price and owner_address are not cleared
                Assert(
                    And(
                        self.ask_price.get() != Int(0),
                        self.owner_address.get() != Global.zero_address(),
                    )
                ),
                # Reset bid offer
                If(
                    self.bid_price.get() != Int(0),
                    Seq([self.bids_amount.put(self.bids_amount.get() - Int(1))]),
                ),
                # Increase bid_price
                If(
                    Gtxn[2].receiver() == self.escrow_address.get(),
                    Seq(
                        [
                            self.bid_price.put(self.bid_price.get() + Gtxn[2].amount()),
                        ]
                    ),
                ),
                # Decrease bid_price
                If(
                    Gtxn[2].sender() == self.escrow_address.get(),
                    Seq(
                        [
                            self.bid_price.put(self.bid_price.get() - Gtxn[2].amount()),
                        ]
                    ),
                ),
                Assert(
                    And(
                        self.bid_price.get() == self.ask_price.get(),
                        # Cover fee
                        Gtxn[1].receiver() == self.escrow_address.get(),
                        # Transfer NFT to a new owner
                        Gtxn[3].sender() == self.escrow_address.get(),
                        # Transfer ALGO to the former owner
                        Gtxn[4].receiver() == self.owner_address.get(),
                        Gtxn[4].sender() == self.escrow_address.get(),
                        Gtxn[4].amount() == self.ask_price.get() * Int(95) / Int(100),
                        Gtxn[5].receiver() == Addr(self.fee_addr1),
                        Gtxn[5].sender() == self.escrow_address.get(),
                        Gtxn[5].amount()
                        == (self.ask_price.get() * Int(5) / Int(100)) / Int(2),
                        Gtxn[6].receiver() == Addr(self.fee_addr2),
                        Gtxn[6].sender() == self.escrow_address.get(),
                        Gtxn[6].amount()
                        == (self.ask_price.get() * Int(5) / Int(100)) / Int(2),
                    )
                ),
                # Reset ask offer
                self.ask_price.put(Int(0)),
                self.owner_address.put(Global.zero_address()),
                self.bid_price.put(Int(0)),
                Return(Int(1)),
            ]
        )

    def on_sell_now(self):
        return Seq(
            [
                Assert(
                    And(
                        # Make sure there's a bid in buyer's account
                        App.localGet(Int(1), Bytes("B")) != Int(0),
                        # Transfer ALGO to the seller
                        Gtxn[2].amount()
                        == App.localGet(Int(1), Bytes("B")) * Int(95) / Int(100),
                        Gtxn[2].sender() == self.escrow_address.get(),
                        # Cover fee
                        Gtxn[1].receiver() == self.escrow_address.get(),
                        Gtxn[4].receiver() == Addr(self.fee_addr1),
                        Gtxn[4].amount()
                        == (App.localGet(Int(1), Bytes("B")) * Int(5) / Int(100))
                        / Int(2),
                        Gtxn[5].receiver() == Addr(self.fee_addr2),
                        Gtxn[5].amount()
                        == (App.localGet(Int(1), Bytes("B")) * Int(5) / Int(100))
                        / Int(2),
                    )
                ),
                # Reset the bidder's offer
                App.localPut(Int(1), Bytes("B"), Int(0)),
                self.bids_amount.put(self.bids_amount.get() - Int(1)),
                # Transfer NFT to a new owner
                Assert(
                    Gtxn[3].asset_receiver() == Txn.accounts[1],
                ),
                If(
                    self.owner_address.get() == Global.zero_address(),
                    Seq(
                        [
                            Assert(
                                Gtxn[3].sender() == Txn.sender(),
                            ),
                            Return(Int(1)),
                        ]
                    ),
                ),
                If(
                    self.owner_address.get() == Txn.sender(),
                    Seq(
                        [
                            Assert(Gtxn[3].sender() == self.escrow_address.get()),
                            # Reset ask offer
                            self.ask_price.put(Int(0)),
                            self.owner_address.put(Global.zero_address()),
                            Return(Int(1)),
                        ]
                    ),
                ),
                Return(Int(0)),
            ]
        )

    def on_create(self):
        return Seq(
            [
                self.nft_id.put(Btoi(Txn.application_args[0])),
                self.owner_address.put(Global.zero_address()),
                self.creator_address.put(Txn.accounts[1]),
                self.escrow_address.put(Global.zero_address()),
                self.ask_price.put(Int(0)),
                self.bids_amount.put(Int(0)),
                self.contract_version.put(Int(self.contract_version_value)),
                Return(Int(1)),
            ]
        )

    def on_closeout(self):
        return Seq(
            [
                Assert(self.bid_price.get() == Int(0)),
                Return(Int(1)),
            ]
        )

    def on_setup_escrow(self):
        return Seq(
            [
                Assert(
                    self.escrow_address.get() == Global.zero_address(),
                ),
                Return(Int(1)),
            ]
        )

    def on_configure(self):
        return Seq(
            [
                # Update escrow address after creating it
                Assert(
                    And(
                        Txn.sender() == self.creator_address.get(),
                        self.escrow_address.get() == Global.zero_address(),
                    )
                ),
                self.escrow_address.put(Txn.accounts[1]),
                Return(Int(1)),
            ]
        )

    def get_contract(self):
        return Seq(
            [
                If(Txn.application_id() == Int(0), self.on_create()),
                Assert(
                    And(
                        Txn.close_remainder_to() == Global.zero_address(),
                        Txn.rekey_to() == Global.zero_address(),
                    )
                ),
                Cond(
                    [Txn.on_completion() == OnComplete.OptIn, self.on_register()],
                    [
                        Txn.on_completion()
                        == Or(
                            OnComplete.UpdateApplication, OnComplete.DeleteApplication
                        ),
                        Return(Int(0)),
                    ],
                    [Txn.on_completion() == OnComplete.CloseOut, self.on_closeout()],
                    [Txn.application_args[0] == Bytes("B"), self.on_bid()],
                    [Txn.application_args[0] == Bytes("S"), self.on_set_price()],
                    [Txn.application_args[0] == Bytes("BN"), self.on_buy_now()],
                    [Txn.application_args[0] == Bytes("SN"), self.on_sell_now()],
                    [Txn.application_args[0] == Bytes("C"), self.on_configure()],
                ),
            ]
        )


def manager(fee_addr1: str, fee_addr2: str, contract_version_value: str):
    return ManagerContract(fee_addr1, fee_addr2, contract_version_value).get_contract()


if __name__ == "__main__":
    params = {
        "fee_addr1": "MQGCPHNUM2LOACZ35R3HGGKEKAPAWOSEGCHKQH5OPOH6A5U2WQD5SYKRTA",
        "fee_addr2": "KFGORPVVRSWB6264OAKTROWZJ2QKJLAGTH7CP2Y2447P5ZFNIVFEKY3TPY",
        "contract_version_value": "1",
    }

    # Overwrite params if sys.argv[1] is passed
    if len(sys.argv) > 1:
        params = parse_params(sys.argv[1], params)

    print(
        compileTeal(
            manager(
                params["fee_addr1"],
                params["fee_addr2"],
                params["contract_version_value"],
            ),
            Mode.Application,
            version=TEAL_VERSION,
        )
    )
