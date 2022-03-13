import sys

from pyteal import (
    Addr,
    And,
    Assert,
    Bytes,
    Cond,
    Global,
    Gtxn,
    If,
    Int,
    Mode,
    Or,
    Return,
    Seq,
    Txn,
    TxnType,
    compileTeal,
)

if __name__ == "__main__":
    from helpers.parse import parse_args
else:
    from .helpers.parse import parse_args


def escrow(app_id: int, nft_id: int, fee_addr1: str, fee_addr2: str):
    on_bid = Seq(
        [
            # Decrease bid_price
            Assert(
                And(
                    Global.group_size() == Int(3),
                    Gtxn[2].type_enum() == TxnType.Payment,
                    Gtxn[2].receiver() == Gtxn[0].sender(),
                    Gtxn[1].type_enum() == TxnType.Payment,
                    Gtxn[1].sender() == Gtxn[0].sender(),
                    Gtxn[1].amount() >= Gtxn[2].fee(),
                )
            ),
            Return(Int(1)),
        ]
    )

    on_buy_now = Seq(
        [
            # Increase or decrease bid_price
            Assert(
                And(
                    Gtxn[2].type_enum() == TxnType.Payment,
                    Or(
                        Gtxn[2].receiver() == Gtxn[0].sender(),
                        Gtxn[2].sender() == Gtxn[0].sender(),
                    ),
                    Global.group_size() == Int(7),
                )
            ),
            # Transfer NFT to a new owner
            Assert(
                And(
                    Gtxn[3].type_enum() == TxnType.AssetTransfer,
                    Gtxn[3].xfer_asset() == Int(nft_id),
                    Gtxn[3].asset_amount() == Int(1),
                )
            ),
            # Transfer USDC to the former owner
            Assert(Gtxn[4].type_enum() == TxnType.Payment),
            # Transfer 5% to creators
            Assert(
                And(
                    Gtxn[5].type_enum() == TxnType.Payment,
                    Gtxn[5].receiver() == Addr(fee_addr1),
                    Gtxn[6].type_enum() == TxnType.Payment,
                    Gtxn[6].receiver() == Addr(fee_addr2),
                )
            ),
            # Check if fee for withdrawal transactions is covered
            Assert(
                And(
                    Gtxn[1].type_enum() == TxnType.Payment,
                    Gtxn[1].sender() == Gtxn[0].sender(),
                )
            ),
            If(
                Gtxn[2].sender() == Gtxn[0].sender(),
                Seq(
                    [
                        Assert(
                            Gtxn[1].amount()
                            >= (
                                Gtxn[3].fee()
                                + Gtxn[4].fee()
                                + Gtxn[5].fee()
                                + Gtxn[6].fee()
                            )
                        ),
                        Return(Int(1)),
                    ]
                ),
            ),
            If(
                Gtxn[2].receiver() == Gtxn[0].sender(),
                Seq(
                    [
                        Assert(
                            Gtxn[1].amount()
                            >= (
                                Gtxn[2].fee()
                                + Gtxn[3].fee()
                                + Gtxn[4].fee()
                                + Gtxn[5].fee()
                                + Gtxn[6].fee()
                            )
                        ),
                        Return(Int(1)),
                    ]
                ),
            ),
            Return(Int(0)),
        ]
    )

    on_sell_now = Seq(
        [
            # Transfer USDC to the seller
            Assert(
                And(
                    Global.group_size() == Int(6),
                    Gtxn[2].type_enum() == TxnType.Payment,
                    Gtxn[2].receiver() == Gtxn[0].sender(),
                )
            ),
            # Transfer NFT to a new owner
            Assert(
                And(
                    Gtxn[3].type_enum() == TxnType.AssetTransfer,
                    Gtxn[3].xfer_asset() == Int(nft_id),
                    Gtxn[3].asset_amount() == Int(1),
                )
            ),
            # Transfer 5% to creators
            Assert(
                And(
                    Gtxn[4].type_enum() == TxnType.Payment,
                    Gtxn[4].receiver() == Addr(fee_addr1),
                    Gtxn[5].type_enum() == TxnType.Payment,
                    Gtxn[5].receiver() == Addr(fee_addr2),
                )
            ),
            # Check if fee for withdrawal transactions is covered
            Assert(
                And(
                    Gtxn[1].type_enum() == TxnType.Payment,
                    Gtxn[1].sender() == Gtxn[0].sender(),
                )
            ),
            If(
                Gtxn[3].sender() == Gtxn[0].sender(),
                Seq(
                    [
                        Assert(
                            Gtxn[1].amount()
                            >= Gtxn[2].fee() + Gtxn[4].fee() + Gtxn[5].fee()
                        ),
                        Return(Int(1)),
                    ]
                ),
            ),
            If(
                Gtxn[3].sender() != Gtxn[0].sender(),
                Seq(
                    [
                        Assert(
                            Gtxn[1].amount()
                            >= Gtxn[2].fee()
                            + Gtxn[3].fee()
                            + Gtxn[4].fee()
                            + Gtxn[5].fee()
                        ),
                        Return(Int(1)),
                    ]
                ),
            ),
            Return(Int(0)),
        ]
    )

    on_configure = Seq(
        [
            Return(Int(1)),
        ]
    )

    on_set_price = Seq(
        [
            Assert(
                And(
                    Global.group_size() == Int(3),
                    # Check if fee for withdrawal transaction is covered
                    Gtxn[1].type_enum() == TxnType.Payment,
                    Gtxn[1].sender() == Gtxn[0].sender(),
                    Gtxn[1].amount() >= Gtxn[2].fee(),
                    # Withdraw NFT token
                    Gtxn[2].type_enum() == TxnType.AssetTransfer,
                    Gtxn[2].xfer_asset() == Int(nft_id),
                    Gtxn[2].asset_amount() == Int(1),
                    Gtxn[2].asset_receiver() == Gtxn[0].sender(),
                )
            ),
            Return(Int(1)),
        ]
    )

    return Seq(
        [
            Assert(
                And(
                    Gtxn[0].application_id() == Int(app_id),
                    Gtxn[0].type_enum() == TxnType.ApplicationCall,
                    Txn.close_remainder_to() == Global.zero_address(),
                    Txn.rekey_to() == Global.zero_address(),
                )
            ),
            Cond(
                [Gtxn[0].application_args[0] == Bytes("S"), on_set_price],
                [Gtxn[0].application_args[0] == Bytes("B"), on_bid],
                [Gtxn[0].application_args[0] == Bytes("BN"), on_buy_now],
                [Gtxn[0].application_args[0] == Bytes("SN"), on_sell_now],
                [Gtxn[0].application_args[0] == Bytes("C"), on_configure],
            ),
        ]
    )


if __name__ == "__main__":
    params = {}

    # Overwrite params if sys.argv[1] is passed
    if len(sys.argv) > 1:
        params = parse_args(sys.argv[1], params)

    print(
        compileTeal(
            escrow(
                int(params["app_id"]),
                int(params["nft_id"]),
            ),
            Mode.Signature,
        )
    )
