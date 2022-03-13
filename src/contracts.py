from algoworld_swapper.asa_to_asa_swapper import (
    AsaToAsaSwapConfig,
    compile_stateless,
    swapper,
)
from pyteal import Mode, compileTeal

from src.auction.clear import clear
from src.auction.escrow import escrow
from src.auction.manager import manager
from src.auction.proxy import proxy


def get_clear_teal():
    return compileTeal(clear(), Mode.Application)


def get_escrow_teal(app_id: int, nft_id: int, fee_address_a: str, fee_address_b: str):
    return compileTeal(
        escrow(app_id, nft_id, fee_address_a, fee_address_b), Mode.Signature
    )


def get_proxy_teal(proxy_id):
    return compileTeal(proxy(proxy_id), Mode.Signature)


def get_manager_teal(fee_address_a: str, fee_address_b: str, contract_version: str):
    return compileTeal(
        manager(fee_address_a, fee_address_b, contract_version),
        Mode.Application,
    )


INCENTIVE_FEE_ADDRESS = "RJVRGSPGSPOG7W3V7IMZZ2BAYCABW3YC5MWGKEOPAEEI5ZK5J2GSF6Y26A"
INCENTIVE_FEE_AMOUNT = 10000


def get_swapper_teal(
    creator_address: str,
    offered_asa_id: int,
    offered_asa_amount: int,
    requested_asa_id: int,
    requested_asa_amount: int,
):
    configuration = AsaToAsaSwapConfig(
        creator_address,
        offered_asa_id,
        offered_asa_amount,
        requested_asa_id,
        requested_asa_amount,
        INCENTIVE_FEE_ADDRESS,
        INCENTIVE_FEE_AMOUNT,
    )

    return compile_stateless(swapper(configuration))
