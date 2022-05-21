import pytest
from algosdk.error import AlgodHTTPError

from src.swapper.asa_to_asa_swapper import (
    compile_stateless,
    swapper,
)
from src.swapper.swap_proxy import SwapProxy, swapper_proxy
from tests.helpers import (
    fund_wallet,
    generate_wallet,
    logic_signature,
)
from tests.helpers.utils import save_proxy_note
from tests.models import AlgorandSandbox, LogicSigWallet, Wallet


@pytest.fixture()
def swap_creator(algorand_sandbox: AlgorandSandbox) -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account, algorand_sandbox)
    print(f"\n --- Swapper Creator {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def swap_proxy(swap_creator: Wallet) -> LogicSigWallet:
    cfg = SwapProxy(
        swap_creator=swap_creator.public_key,
    )

    swapper_proxy_lsig = logic_signature(compile_stateless(swapper_proxy(cfg)))

    return LogicSigWallet(
        logicsig=swapper_proxy_lsig, public_key=swapper_proxy_lsig.address()
    )


def test_swapper_asa_optin(swap_creator: Wallet, swap_proxy: LogicSigWallet):
    save_proxy_note(swap_creator, swap_proxy, "aws_gotta_save_this")
