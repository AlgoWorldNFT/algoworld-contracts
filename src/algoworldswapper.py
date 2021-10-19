import dataclasses
import sys

from pyteal import (Addr, And, Cond, Global, Gtxn, Int, Mode, TxnType,
                    compileTeal)

from src.utils import parse_params

"""
The AlgoWorld Cards Atomic Swapper
1. Offered Card Opt-In
2. Offered Card / Required Card Swap
3. Close Swap
"""

TEAL_VERSION = 5

MAX_FEE = Int(1000)

CARD_OPTIN_GSIZE = Int(2)
CARD_OPTIN_FEE = 0
CARD_OPTIN = 1

CARD_DEPOSIT_GSIZE = Int(1)
CARD_DEPOSIT = 0

CARDS_SWAP_GSIZE = Int(2)
OFFERED_CARD_XFER = 0
REQUIRED_CARD_XFER = 1

CLOSE_SWAP_GSIZE = Int(3)
CARD_CLOSE = 0
SWAP_CLOSE = 1
PROOF = 2


@dataclasses.dataclass
class SwapConfig:
    swap_creator: str
    offered_card_id: int
    required_card_id: int
    optin_last_valid_block: int


def swapper(cfg: SwapConfig):

    is_card_optin = And(
        Global.group_size() == CARD_OPTIN_GSIZE,
        Gtxn[CARD_OPTIN_FEE].type_enum() == TxnType.Payment,
        Gtxn[CARD_OPTIN].type_enum() == TxnType.AssetTransfer,
    )

    is_card_deposit = And(
        Global.group_size() == CARD_DEPOSIT_GSIZE,
        Gtxn[CARD_DEPOSIT].type_enum() == TxnType.AssetTransfer
    )

    is_cards_swap = And(
        Global.group_size() == CARDS_SWAP_GSIZE,
        Gtxn[OFFERED_CARD_XFER].type_enum() == TxnType.AssetTransfer,
        Gtxn[REQUIRED_CARD_XFER].type_enum() == TxnType.AssetTransfer,
    )

    is_close_swap = And(
        Global.group_size() == CLOSE_SWAP_GSIZE,
        Gtxn[CARD_CLOSE].type_enum() == TxnType.AssetTransfer,
        Gtxn[SWAP_CLOSE].type_enum() == TxnType.Payment,
        Gtxn[PROOF].type_enum() == TxnType.Payment,
    )

    return Cond(
        [is_card_optin, card_optin(cfg)],
        [is_card_deposit, card_optin(cfg)],
        [is_cards_swap, cards_swap(cfg)],
        [is_close_swap, close_swap(cfg)],
    )


def card_optin(cfg: SwapConfig):

    card_xfer_fee_precondition = And(
        Gtxn[CARD_OPTIN_FEE].fee() <= MAX_FEE,
        Gtxn[CARD_OPTIN_FEE].receiver() == Gtxn[CARD_OPTIN].sender(),
        Gtxn[CARD_OPTIN_FEE].close_remainder_to() == Global.zero_address(),
        Gtxn[CARD_OPTIN_FEE].rekey_to() == Global.zero_address(),
    )
    card_xfer_precondition = And(
        Gtxn[CARD_OPTIN].fee() <= MAX_FEE,
        Gtxn[CARD_OPTIN].asset_sender() == Global.zero_address(),
        Gtxn[CARD_OPTIN].asset_close_to() == Global.zero_address(),
        Gtxn[CARD_OPTIN].rekey_to() == Global.zero_address(),
    )

    return And(
        card_xfer_fee_precondition,
        card_xfer_precondition,
        Gtxn[CARD_OPTIN].xfer_asset() == Int(cfg.offered_card_id),
        Gtxn[CARD_OPTIN].asset_amount() == Int(0),
        Gtxn[CARD_OPTIN].sender() == Gtxn[CARD_OPTIN].asset_receiver(),
        Gtxn[CARD_OPTIN].last_valid() < Int(cfg.optin_last_valid_block)
    )

def is_card_deposit(cfg: SwapConfig):

    card_deposit_precondition = And(
        Gtxn[CARD_DEPOSIT].fee() <= MAX_FEE,
        Gtxn[CARD_DEPOSIT].asset_sender() == Global.zero_address(),
        Gtxn[CARD_DEPOSIT].asset_close_to() == Global.zero_address(),
        Gtxn[CARD_DEPOSIT].rekey_to() == Global.zero_address(),
    )

    return And(
        card_deposit_precondition,
        Gtxn[CARD_DEPOSIT].xfer_asset() == Int(cfg.offered_card_id),
        Gtxn[CARD_DEPOSIT].asset_amount() >= Int(1),
        Gtxn[CARD_DEPOSIT].sender() == cfg.swap_creator,
        Gtxn[CARD_DEPOSIT].last_valid() < Int(cfg.optin_last_valid_block)
    )

def cards_swap(cfg: SwapConfig):

    offered_card_xfer_precondition = And(
        Gtxn[OFFERED_CARD_XFER].fee() <= MAX_FEE,
        Gtxn[OFFERED_CARD_XFER].asset_sender() == Global.zero_address(),
        Gtxn[OFFERED_CARD_XFER].asset_close_to() == Global.zero_address(),
        Gtxn[OFFERED_CARD_XFER].rekey_to() == Global.zero_address(),
    )

    required_card_xfer_precondition = And(
        Gtxn[REQUIRED_CARD_XFER].asset_sender() == Global.zero_address(),
    )

    return And(
        offered_card_xfer_precondition,
        required_card_xfer_precondition,

        Gtxn[OFFERED_CARD_XFER].xfer_asset() == Int(cfg.offered_card_id),
        Gtxn[OFFERED_CARD_XFER].asset_amount() == Int(1),

        Gtxn[REQUIRED_CARD_XFER].xfer_asset() == Int(cfg.required_card_id),
        Gtxn[REQUIRED_CARD_XFER].asset_amount() == Int(1),

        Gtxn[OFFERED_CARD_XFER].asset_receiver() == Gtxn[REQUIRED_CARD_XFER].sender(),
        Gtxn[REQUIRED_CARD_XFER].asset_receiver() == Addr(cfg.swap_creator),
    )


def close_swap(cfg: SwapConfig):

    card_close_precondition = And(
        Gtxn[CARD_CLOSE].fee() <= MAX_FEE,
        Gtxn[CARD_CLOSE].asset_sender() == Global.zero_address(),
        Gtxn[CARD_CLOSE].rekey_to() == Global.zero_address(),
    )

    swap_close_precondition = And(
        Gtxn[CARD_CLOSE].fee() <= MAX_FEE,
        Gtxn[CARD_CLOSE].rekey_to() == Global.zero_address(),
    )

    return And(
        card_close_precondition,
        swap_close_precondition,

        Gtxn[CARD_CLOSE].xfer_asset() == Int(cfg.offered_card_id),
        Gtxn[CARD_CLOSE].asset_receiver() == Addr(cfg.swap_creator),
        Gtxn[CARD_CLOSE].asset_close_to() == Addr(cfg.swap_creator),

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
        "offered_card_id": 42,
        "required_card_id": 69,
        "optin_last_valid_block": 420
    }

    # Overwrite params if sys.argv[1] is passed
    if(len(sys.argv) > 1):
        params = parse_params(sys.argv[1], params)

    print(compile_stateless(swapper(SwapConfig(**params))))
