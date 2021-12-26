import dataclasses
import sys

from pyteal import Addr, And, Cond, Global, Gtxn, Int, Mode, TxnType, compileTeal

from src.utils import parse_params

"""
ASA Atomic Swapper
1. Offered ASA Opt-In
2. Offered ASA / Required ASA Swap
3. Close Swap
"""

TEAL_VERSION = 5

MAX_FEE = Int(1000)
OPTIN_FUNDING_AMOUNT = 210000
INCENTIVE_FEE_AMOUNT = 10000
INCENTIVE_FEE_ADDRESS = "RJVRGSPGSPOG7W3V7IMZZ2BAYCABW3YC5MWGKEOPAEEI5ZK5J2GSF6Y26A"

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
class SwapConfig:
    swap_creator: str
    offered_asa_id: int
    offered_asa_amount: int
    requested_asa_id: int
    requested_asa_amount: int


def swapper(cfg: SwapConfig):

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


def asa_optin(cfg: SwapConfig):

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


def asa_swap(cfg: SwapConfig):

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
        Gtxn[INCENTIVE_FEE].receiver() == Addr(INCENTIVE_FEE_ADDRESS),
        Gtxn[INCENTIVE_FEE].sender() == Gtxn[REQUESTED_ASA_XFER].sender(),
        Gtxn[INCENTIVE_FEE].amount() == Int(INCENTIVE_FEE_AMOUNT),
    )


def close_swap(cfg: SwapConfig):

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
    }

    # Overwrite params if sys.argv[1] is passed
    if len(sys.argv) > 1:
        params = parse_params(sys.argv[1], params)

    print(compile_stateless(swapper(SwapConfig(**params))))
