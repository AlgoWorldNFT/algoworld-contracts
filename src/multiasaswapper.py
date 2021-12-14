import dataclasses

from pyteal import Approve, And, Cond, Global, Gtxn, Int, Mode, TxnType, compileTeal

"""
Multi ASA Atomic Swapper
1. Offered ASA Group Opt-In
2. Offered ASA Gorup / Required ALGO Multi Swap
3. Close Multi Swap
"""

TEAL_VERSION = 5


@dataclasses.dataclass
class MultiSwapConfig:
    multi_asa_swap_creator: str
    offered_asa_group: dict
    requested_algo_amount: int


def multi_asa_swapper(cfg: MultiSwapConfig):

    MULTI_ASA_SWAP_SIZE = len(cfg.offered_asa_group)

    ASA_OPTIN_GSIZE = Int(MULTI_ASA_SWAP_SIZE + 1)
    OPTIN_FEE = 0

    asa_group_optin = []
    for asa in range(MULTI_ASA_SWAP_SIZE):
        asa_group_optin += [Gtxn[asa + 1].type_enum() == TxnType.AssetTransfer]

    is_asa_optin = And(
        Global.group_size() == ASA_OPTIN_GSIZE,
        Gtxn[OPTIN_FEE].type_enum() == TxnType.Payment,
        *asa_group_optin,
    )

    return Cond(
        [is_asa_optin, Approve()],
    )


def compile_stateless(program):
    return compileTeal(program, Mode.Signature, version=TEAL_VERSION)


if __name__ == "__main__":

    offered_asa_group = {
        'asa_1': 10,
        'asa_2': 10,
    }

    config = MultiSwapConfig(
        "2ILRL5YU3FZ4JDQZQVXEZUYKEWF7IEIGRRCPCMI36VKSGDMAS6FHSBXZDQ",
        offered_asa_group,
        1000,
    )

    print(compile_stateless(multi_asa_swapper(config)))
