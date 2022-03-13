import pytest
from algosdk.error import AlgodHTTPError

from src.swapper.asa_to_asa_swapper import OPTIN_FUNDING_AMOUNT
from tests.common import fund_wallet, generate_wallet, swapper_opt_in
from tests.models import AlgorandSandbox, LogicSigWallet, Wallet


@pytest.fixture()
def main_account(algorand_sandbox: AlgorandSandbox) -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account, algorand_sandbox)
    print(f"\n --- Swapper Creator {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def creator_account(algorand_sandbox: AlgorandSandbox) -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account, algorand_sandbox)
    print(f"\n --- Swapper Creator {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def buyer_account(algorand_sandbox: AlgorandSandbox) -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account, algorand_sandbox)
    print(f"\n --- Swapper Creator {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def fee_profits_a_account(algorand_sandbox: AlgorandSandbox) -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account, algorand_sandbox)
    print(f"\n --- Swapper Creator {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def fee_profits_b_account(algorand_sandbox: AlgorandSandbox) -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account, algorand_sandbox)
    print(f"\n --- Swapper Creator {funded_account.public_key} funded.")
    return funded_account


def test_auction_flow(
    swapper_account: LogicSigWallet,
    swap_creator: Wallet,
    swap_user: Wallet,
    offered_asa_idx: int,
    other_asa_idx: int,
):

    with pytest.raises(AlgodHTTPError):
        print("\n --- Opt-In fails if not executed by swap creator")
        swapper_opt_in(
            swap_creator=swap_user,
            swapper_account=swapper_account,
            assets={offered_asa_idx: 0},
            funding_amount=OPTIN_FUNDING_AMOUNT,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Opt-In fails with wrong funding amount")
        swapper_opt_in(
            swap_creator=swap_creator,
            swapper_account=swapper_account,
            assets={offered_asa_idx: 0},
            funding_amount=OPTIN_FUNDING_AMOUNT - 1,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Opt-In fails with wrong ASA")
        swapper_opt_in(
            swap_creator=swap_creator,
            swapper_account=swapper_account,
            assets={other_asa_idx: 0},
            funding_amount=OPTIN_FUNDING_AMOUNT,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Opt-In fails with wrong ASA amount")
        swapper_opt_in(
            swap_creator=swap_creator,
            swapper_account=swapper_account,
            assets={offered_asa_idx: 1},
            funding_amount=OPTIN_FUNDING_AMOUNT,
        )

    # Happy path
    swapper_opt_in(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_idx: 0},
        funding_amount=OPTIN_FUNDING_AMOUNT,
    )
