import pytest
from algosdk.error import AlgodHTTPError

from algoworld_contracts.swapper.swap_proxy import (
    SwapProxy,
    compile_stateless,
    swapper_proxy,
)
from tests.helpers import fund_wallet, generate_wallet, logic_signature
from tests.helpers.constants import SWAP_PROXY_VERSION
from tests.helpers.utils import activate_or_save_proxy_note
from tests.models import AlgorandSandbox, LogicSigWallet, Wallet


@pytest.fixture()
def swap_creator(algorand_sandbox: AlgorandSandbox) -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account, algorand_sandbox)
    print(f"\n --- Swapper Creator {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def swap_proxy(swap_creator: Wallet) -> LogicSigWallet:
    cfg = SwapProxy(swap_creator=swap_creator.public_key, version=SWAP_PROXY_VERSION)

    swapper_proxy_lsig = logic_signature(compile_stateless(swapper_proxy(cfg)))

    return LogicSigWallet(
        logicsig=swapper_proxy_lsig, public_key=swapper_proxy_lsig.address()
    )


def test_swap_proxy_activate_or_save(swap_creator, swap_proxy):
    # first txn is activation (should fail if less than 110_000 provided)
    with pytest.raises(AlgodHTTPError):
        activate_or_save_proxy_note(
            swap_creator, swap_proxy, "gotta_save_this", 10_000, 0
        )

    # first txn is activation
    activate_or_save_proxy_note(
        swap_creator, swap_proxy, "ipfs://_gotta_save_this", 110_000, 0
    )

    # second txn is store operation
    activate_or_save_proxy_note(
        swap_creator, swap_proxy, "ipfs://_gotta_save_this", 10_000, 0
    )

    # rest are additional edge cases to cover
    with pytest.raises(AlgodHTTPError):
        activate_or_save_proxy_note(
            swap_creator, swap_proxy, "gotta_save_this", 10_000, 0
        )

    with pytest.raises(AlgodHTTPError):
        activate_or_save_proxy_note(
            swap_proxy, swap_creator, "ipfs://_gotta_save_this", 10_000, 0
        )

    with pytest.raises(AlgodHTTPError):
        activate_or_save_proxy_note(
            swap_creator, swap_proxy, "ipfs://_gotta_save_this", 10_000, 1
        )

    with pytest.raises(AlgodHTTPError):
        activate_or_save_proxy_note(
            swap_creator, swap_proxy, "ipfs://_gotta_save_this", 0, 10
        )
