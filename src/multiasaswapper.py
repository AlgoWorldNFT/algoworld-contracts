import dataclasses

from pyteal import Addr, And, Cond, Expr, Global, Gtxn, Int, Mode, TxnType, compileTeal

"""
Multi ASA Atomic Swapper
1. Multi ASA Opt-In
2. Offered Multi ASA / Requested ALGO Swap
3. Close Multi ASA Swap
"""

TEAL_VERSION = 5


@dataclasses.dataclass
class MultiAsaSwapConfig:
    swap_creator: str
    offered_asa_amounts: dict[str, int]
    requested_algo_amount: int
    max_fee: int
    optin_funding_amount: int
    incentive_fee_amount: int
    incentive_fee_address: str

    def __post_init__(self):
        assert len(self.offered_asa_amounts) <= 5
        self.body_size = len(self.offered_asa_amounts)

        # MULTI ASA OPTIN
        self.optin_header = {
            'fee': 0,
        }
        self.optin_bottom = {}
        self.optin_gsize = len(
            self.optin_header) + self.body_size + len(
            self.optin_bottom)

        # MULTI ASA SWAP
        self.swap_header = {
            'incentive_fee': 0,
            'requested_algo_xfer': 1,
        }
        self.swap_bottom = {}
        self.swap_gsize = len(
            self.swap_header) + self.body_size + len(
            self.swap_bottom)

        # CLOSE MULTI ASA SWAP
        self.close_swap_header = {}
        self.close_swap_bottom = {
            'close_out': self.body_size + 0,
            'proof': self.body_size + 1,
        }
        self.close_swap_gsize = len(
            self.close_swap_header) + self.body_size + len(
            self.close_swap_bottom)


def multi_asa_swapper(cfg: MultiAsaSwapConfig) -> Expr:

    multi_asa_optin_type_check = [
        Gtxn[len(cfg.optin_header) + asa].type_enum() == TxnType.AssetTransfer
        for asa in range(cfg.body_size)
    ]

    is_multi_asa_optin = And(
        Global.group_size() == Int(cfg.optin_gsize),
        Gtxn[cfg.optin_header['fee']].type_enum() == TxnType.Payment,
        *multi_asa_optin_type_check,
    )

    multi_asa_xfer_type_check = [
        Gtxn[len(cfg.swap_header) + asa].type_enum() == TxnType.AssetTransfer
        for asa in range(cfg.body_size)
    ]

    is_multi_asa_swap = And(
        Global.group_size() == Int(cfg.swap_gsize),
        Gtxn[cfg.swap_header['incentive_fee']].type_enum() == TxnType.Payment,
        Gtxn[cfg.swap_header['requested_algo_xfer']].type_enum() == TxnType.Payment,
        *multi_asa_xfer_type_check,
    )

    multi_asa_close_type_check = [
        Gtxn[len(cfg.close_swap_header) + asa].type_enum() == TxnType.AssetTransfer
        for asa in range(cfg.body_size)
    ]

    is_close_swap = And(
        Global.group_size() == Int(cfg.close_swap_gsize),
        *multi_asa_close_type_check,
        Gtxn[cfg.close_swap_bottom['close_out']].type_enum() == TxnType.Payment,
        Gtxn[cfg.close_swap_bottom['proof']].type_enum() == TxnType.Payment,
    )

    return Cond(
        [is_multi_asa_optin, multi_asa_optin(cfg)],
        [is_multi_asa_swap, multi_asa_swap(cfg)],
        [is_close_swap, multi_asa_close_swap(cfg)],
    )


def multi_asa_optin(cfg: MultiAsaSwapConfig):

    # Code repetition of `for asa in range(cfg.body_size)` for every check
    # has been kept in favor of readability. A unique for loop would be more
    # succint but maybe harder to read.

    multi_asa_optin_max_fee = [
        Gtxn[len(cfg.optin_header) + asa].fee() <= Int(cfg.max_fee)
        for asa in range(cfg.body_size)
    ]

    multi_asa_optin_rekey_to = [
        Gtxn[len(cfg.optin_header) + asa].rekey_to() == Global.zero_address()
        for asa in range(cfg.body_size)
    ]

    multi_asa_optin_asset_sender = [
        Gtxn[len(cfg.optin_header) + asa].asset_sender() == Global.zero_address()
        for asa in range(cfg.body_size)
    ]

    multi_asa_optin_asset_close_to = [
        Gtxn[len(cfg.optin_header) + asa].asset_close_to() == Global.zero_address()
        for asa in range(cfg.body_size)
    ]

    # The following check implies all the ASA xfers have the same sender
    multi_asa_optin_senders = [
        Gtxn[len(cfg.optin_header) + asa].sender() == Gtxn[cfg.optin_header['fee']].receiver()
        for asa in range(cfg.body_size)
    ]

    asa = 0
    multi_asa_optin_xfer_asset = []
    for k in cfg.offered_asa_amounts:
        multi_asa_optin_xfer_asset += [
            Gtxn[len(cfg.optin_header) + asa].xfer_asset() == Int(int(k))
        ]
        asa += 1

    multi_asa_optin_assets_receivers = [
        Gtxn[len(cfg.optin_header) + asa].sender() == Gtxn[len(cfg.optin_header) + asa].asset_receiver()
        for asa in range(cfg.body_size)
    ]

    multi_asa_optin_assets_amounts = [
        Gtxn[len(cfg.optin_header) + asa].asset_amount() == Int(0)
        for asa in range(cfg.body_size)
    ]

    optin_funding_precondition = And(
        Gtxn[cfg.optin_header['fee']].fee() <= Int(cfg.max_fee),
        Gtxn[cfg.optin_header['fee']].rekey_to() == Global.zero_address(),
        Gtxn[cfg.optin_header['fee']].close_remainder_to() == Global.zero_address(),
    )

    multi_asa_optin_precondition = And(
        *multi_asa_optin_max_fee,
        *multi_asa_optin_rekey_to,
        *multi_asa_optin_asset_sender,
        *multi_asa_optin_asset_close_to,
    )

    return And(
        optin_funding_precondition,
        multi_asa_optin_precondition,
        Gtxn[cfg.optin_header['fee']].sender() == Addr(cfg.swap_creator),
        Gtxn[cfg.optin_header['fee']].amount() >= Int(cfg.optin_funding_amount),
        *multi_asa_optin_senders,
        *multi_asa_optin_xfer_asset,
        *multi_asa_optin_assets_receivers,
        *multi_asa_optin_assets_amounts,
    )


def multi_asa_swap(cfg: MultiAsaSwapConfig):

    offered_multi_asa_xfer_max_fee = [
        Gtxn[len(cfg.swap_header) + asa].fee() <= Int(cfg.max_fee)
        for asa in range(cfg.body_size)
    ]

    offered_multi_asa_xfer_rekey_to = [
        Gtxn[len(cfg.swap_header) + asa].rekey_to() == Global.zero_address()
        for asa in range(cfg.body_size)
    ]

    offered_multi_asa_xfer_asset_sender = [
        Gtxn[len(cfg.swap_header) + asa].asset_sender() == Global.zero_address()
        for asa in range(cfg.body_size)
    ]

    offered_multi_asa_xfer_asset_close_to = [
        Gtxn[len(cfg.swap_header) + asa].asset_close_to() == Global.zero_address()
        for asa in range(cfg.body_size)
    ]

    asa = 0
    offered_multi_asa_xfer_asset_ids = []
    offered_multi_asa_xfer_asset_amounts = []
    for k, v in cfg.offered_asa_amounts.items():
        offered_multi_asa_xfer_asset_ids += [
            Gtxn[len(cfg.swap_header) + asa].xfer_asset() == Int(int(k))
        ]
        offered_multi_asa_xfer_asset_amounts += [
            Gtxn[len(cfg.swap_header) + asa].asset_amount() == Int(int(v))
        ]
        asa += 1

    offered_multi_asa_xfer_asset_receiver = [
        Gtxn[len(cfg.swap_header) + asa].asset_receiver() == Gtxn[
            cfg.swap_header['requested_algo_xfer']].sender()
        for asa in range(cfg.body_size)
    ]

    offered_multi_asa_xfer_precondition = And(
        *offered_multi_asa_xfer_max_fee,
        *offered_multi_asa_xfer_rekey_to,
        *offered_multi_asa_xfer_asset_sender,
        *offered_multi_asa_xfer_asset_close_to,
    )

    return And(
        offered_multi_asa_xfer_precondition,
        Gtxn[cfg.swap_header['incentive_fee']].receiver() == Addr(cfg.incentive_fee_address),
        Gtxn[cfg.swap_header['incentive_fee']].amount() == Int(cfg.incentive_fee_amount),
        Gtxn[cfg.swap_header['requested_algo_xfer']].amount() == Int(cfg.requested_algo_amount),
        Gtxn[cfg.swap_header['requested_algo_xfer']].receiver() == Addr(cfg.swap_creator),
        *offered_multi_asa_xfer_asset_ids,
        *offered_multi_asa_xfer_asset_amounts,
        *offered_multi_asa_xfer_asset_receiver,
    )


def multi_asa_close_swap(cfg: MultiAsaSwapConfig):

    multi_asa_close_max_fee = [
        Gtxn[len(cfg.close_swap_header) + asa].fee() <= Int(cfg.max_fee)
        for asa in range(cfg.body_size)
    ]

    multi_asa_close_rekey_to = [
        Gtxn[len(cfg.close_swap_header) + asa].rekey_to() == Global.zero_address()
        for asa in range(cfg.body_size)
    ]

    multi_asa_close_asset_sender = [
        Gtxn[len(cfg.close_swap_header) + asa].asset_sender() == Global.zero_address()
        for asa in range(cfg.body_size)
    ]

    asa = 0
    multi_asa_close_asset_ids = []
    for k, v in cfg.offered_asa_amounts.items():
        multi_asa_close_asset_ids += [
            Gtxn[len(cfg.close_swap_header) + asa].xfer_asset() == Int(int(k))
        ]
        asa += 1

    multi_asa_close_asset_receiver = [
        Gtxn[len(cfg.close_swap_header) + asa].asset_receiver() == Addr(cfg.swap_creator)
        for asa in range(cfg.body_size)
    ]

    multi_asa_close_asset_close_to = [
        Gtxn[len(cfg.close_swap_header) + asa].asset_close_to() == Addr(cfg.swap_creator)
        for asa in range(cfg.body_size)
    ]

    asa_close_precondition = And(
        *multi_asa_close_max_fee,
        *multi_asa_close_rekey_to,
        *multi_asa_close_asset_sender,
    )

    swap_close_precondition = And(
        Gtxn[cfg.close_swap_bottom['close_out']].fee() <= Int(cfg.max_fee),
        Gtxn[cfg.close_swap_bottom['close_out']].rekey_to() == Global.zero_address(),
    )

    return And(
        asa_close_precondition,
        swap_close_precondition,
        *multi_asa_close_asset_ids,
        *multi_asa_close_asset_receiver,
        *multi_asa_close_asset_close_to,
        Gtxn[cfg.close_swap_bottom['close_out']].receiver() == Addr(cfg.swap_creator),
        Gtxn[cfg.close_swap_bottom['close_out']].close_remainder_to() == Addr(cfg.swap_creator),
        Gtxn[cfg.close_swap_bottom['proof']].sender() == Addr(cfg.swap_creator),
        Gtxn[cfg.close_swap_bottom['proof']].receiver() == Addr(cfg.swap_creator),
        Gtxn[cfg.close_swap_bottom['proof']].amount() == Int(0),
    )


def compile_stateless(program):
    return compileTeal(program, Mode.Signature, version=TEAL_VERSION)


if __name__ == "__main__":

    offered_asa_amounts = {
        '1': 10,
        '2': 10,
    }

    config = MultiAsaSwapConfig(
        swap_creator="2ILRL5YU3FZ4JDQZQVXEZUYKEWF7IEIGRRCPCMI36VKSGDMAS6FHSBXZDQ",
        offered_asa_amounts=offered_asa_amounts,
        requested_algo_amount=1_000_000,
        max_fee=1_000,
        optin_funding_amount=210_000,
        incentive_fee_amount=10_000,
        incentive_fee_address="2ILRL5YU3FZ4JDQZQVXEZUYKEWF7IEIGRRCPCMI36VKSGDMAS6FHSBXZDQ",
    )

    print(compile_stateless(multi_asa_swapper(config)))
