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
