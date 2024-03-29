import pytest
from algosdk.error import AlgodHTTPError

from algoworld_contracts.swapper.asa_to_asa_swapper import (
    OPTIN_FUNDING_AMOUNT,
    AsaToAsaSwapConfig,
    compile_stateless,
    swapper,
)
from tests.helpers import (
    INCENTIVE_FEE_ADDRESS,
    asa_to_asa_swap,
    close_swap,
    fund_wallet,
    generate_wallet,
    logic_signature,
    mint_asa,
    opt_in_asa,
    swapper_deposit,
    swapper_opt_in,
)
from tests.models import AlgorandSandbox, LogicSigWallet, Wallet


@pytest.fixture()
def swap_creator(algorand_sandbox: AlgorandSandbox) -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account, algorand_sandbox)
    print(f"\n --- Swapper Creator {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def swap_user(algorand_sandbox: AlgorandSandbox) -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account, algorand_sandbox)
    print(f"\n --- Swapper User {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def incentive_wallet(algorand_sandbox: AlgorandSandbox) -> Wallet:
    incentive_account = Wallet("", INCENTIVE_FEE_ADDRESS)
    fund_wallet(incentive_account, algorand_sandbox)
    print(f"\n --- Incentive Wallet {incentive_account.public_key} funded.")
    return incentive_account


@pytest.fixture()
def offered_asa_idx(swap_creator: Wallet) -> int:
    return mint_asa(
        swap_creator.public_key,
        swap_creator.private_key,
        asset_name="Card A",
        total=1,
        decimals=0,
    )


@pytest.fixture()
def requested_asa_idx(swap_user: Wallet) -> int:
    return mint_asa(
        swap_user.public_key,
        swap_user.private_key,
        asset_name="Card B",
        total=1,
        decimals=0,
    )


@pytest.fixture()
def other_asa_idx(swap_user: Wallet) -> int:
    return mint_asa(
        swap_user.public_key,
        swap_user.private_key,
        asset_name="Other ASA",
        total=1,
        decimals=0,
    )


@pytest.fixture()
def swapper_account(
    swap_creator: Wallet, offered_asa_idx: int, requested_asa_idx: int
) -> LogicSigWallet:
    cfg = AsaToAsaSwapConfig(
        swap_creator=swap_creator.public_key,
        offered_asa_id=offered_asa_idx,
        offered_asa_amount=1,
        requested_asa_id=requested_asa_idx,
        requested_asa_amount=1,
        incentive_fee_address="RJVRGSPGSPOG7W3V7IMZZ2BAYCABW3YC5MWGKEOPAEEI5ZK5J2GSF6Y26A",
        incentive_fee_amount=10_000,
    )

    swapper_lsig = logic_signature(compile_stateless(swapper(cfg)))

    return LogicSigWallet(logicsig=swapper_lsig, public_key=swapper_lsig.address())


def test_swapper_asa_optin(
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


def test_swapper_asa_swap(
    swapper_account: LogicSigWallet,
    swap_creator: Wallet,
    swap_user: Wallet,
    incentive_wallet: Wallet,
    offered_asa_idx: int,
    requested_asa_idx: int,
    other_asa_idx: int,
):
    opt_in_asa(swap_creator, [requested_asa_idx, other_asa_idx])
    opt_in_asa(swap_user, [offered_asa_idx])

    swapper_opt_in(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_idx: 0},
        funding_amount=OPTIN_FUNDING_AMOUNT,
    )

    swapper_deposit(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_idx: 1},
    )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong requested asset ID")
        asa_to_asa_swap(
            offered_asset_sender=swapper_account,
            offered_asset_receiver=swap_user,
            offered_assets={offered_asa_idx: 1},
            requested_asset_sender=swap_user,
            requested_asset_receiver=swap_creator,
            requested_assets={other_asa_idx: 1},
            incentive_wallet=incentive_wallet,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong offered asset amount")
        asa_to_asa_swap(
            offered_asset_sender=swapper_account,
            offered_asset_receiver=swap_user,
            offered_assets={offered_asa_idx: 0},
            requested_asset_sender=swap_user,
            requested_asset_receiver=swap_creator,
            requested_assets={requested_asa_idx: 1},
            incentive_wallet=incentive_wallet,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong requested asset amount")
        asa_to_asa_swap(
            offered_asset_sender=swapper_account,
            offered_asset_receiver=swap_user,
            offered_assets={offered_asa_idx: 1},
            requested_asset_sender=swap_user,
            requested_asset_receiver=swap_creator,
            requested_assets={requested_asa_idx: 0},
            incentive_wallet=incentive_wallet,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong requested asset receiver")
        asa_to_asa_swap(
            offered_asset_sender=swapper_account,
            offered_asset_receiver=swap_user,
            offered_assets={offered_asa_idx: 1},
            requested_asset_sender=swap_user,
            requested_asset_receiver=swap_user,
            requested_assets={requested_asa_idx: 1},
            incentive_wallet=incentive_wallet,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong incentive algo receiver")
        asa_to_asa_swap(
            offered_asset_sender=swapper_account,
            offered_asset_receiver=swap_user,
            offered_assets={offered_asa_idx: 1},
            requested_asset_sender=swap_user,
            requested_asset_receiver=swap_user,
            requested_assets={requested_asa_idx: 1},
            incentive_wallet=swap_user,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong incentive algo amount")
        asa_to_asa_swap(
            offered_asset_sender=swapper_account,
            offered_asset_receiver=swap_user,
            offered_assets={offered_asa_idx: 1},
            requested_asset_sender=swap_user,
            requested_asset_receiver=swap_user,
            requested_assets={requested_asa_idx: 1},
            incentive_wallet=incentive_wallet,
            incentive_amount=2000,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong requested asa sender")
        asa_to_asa_swap(
            offered_asset_sender=swapper_account,
            offered_asset_receiver=swap_user,
            offered_assets={offered_asa_idx: 1},
            requested_asset_sender=swapper_account,
            requested_asset_receiver=swap_creator,
            requested_assets={requested_asa_idx: 1},
            incentive_wallet=incentive_wallet,
        )

    # Happy path
    asa_to_asa_swap(
        offered_asset_sender=swapper_account,
        offered_asset_receiver=swap_user,
        offered_assets={offered_asa_idx: 1},
        requested_asset_sender=swap_user,
        requested_asset_receiver=swap_creator,
        requested_assets={requested_asa_idx: 1},
        incentive_wallet=incentive_wallet,
    )


def test_swapper_close_swap(
    swapper_account: LogicSigWallet,
    swap_creator: Wallet,
    swap_user: Wallet,
    offered_asa_idx: int,
    other_asa_idx: int,
):
    opt_in_asa(swap_creator, [other_asa_idx])
    opt_in_asa(swap_user, [offered_asa_idx])

    swapper_opt_in(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_idx: 0},
        funding_amount=OPTIN_FUNDING_AMOUNT * 2,
    )

    swapper_deposit(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_idx: 1},
    )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Close swap fails with wrong asset receiver")
        close_swap(
            asset_sender=swapper_account,
            asset_receiver=swap_user,
            asset_close_to=swap_creator,
            asset_ids=[offered_asa_idx],
            swapper_funds_sender=swapper_account,
            swapper_funds_receiver=swap_creator,
            swapper_funds_close_to=swap_creator,
            proof_sender=swap_creator,
            proof_receiver=swap_creator,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Close swap fails with wrong asset close to")
        close_swap(
            asset_sender=swapper_account,
            asset_receiver=swap_creator,
            asset_close_to=swap_user,
            asset_ids=[offered_asa_idx],
            swapper_funds_sender=swapper_account,
            swapper_funds_receiver=swap_creator,
            swapper_funds_close_to=swap_creator,
            proof_sender=swap_creator,
            proof_receiver=swap_creator,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Close swap fails with wrong assets")
        close_swap(
            asset_sender=swapper_account,
            asset_receiver=swap_creator,
            asset_close_to=swap_creator,
            asset_ids=[other_asa_idx],
            swapper_funds_sender=swapper_account,
            swapper_funds_receiver=swap_creator,
            swapper_funds_close_to=swap_creator,
            proof_sender=swap_creator,
            proof_receiver=swap_creator,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Close swap fails with wrong funds receiver")
        close_swap(
            asset_sender=swapper_account,
            asset_receiver=swap_creator,
            asset_close_to=swap_creator,
            asset_ids=[offered_asa_idx],
            swapper_funds_sender=swapper_account,
            swapper_funds_receiver=swap_user,
            swapper_funds_close_to=swap_creator,
            proof_sender=swap_creator,
            proof_receiver=swap_creator,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Close swap fails with wrong funds close to")
        close_swap(
            asset_sender=swapper_account,
            asset_receiver=swap_creator,
            asset_close_to=swap_creator,
            asset_ids=[offered_asa_idx],
            swapper_funds_sender=swapper_account,
            swapper_funds_receiver=swap_creator,
            swapper_funds_close_to=swap_user,
            proof_sender=swap_creator,
            proof_receiver=swap_creator,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Close swap fails with wrong proof sender")
        close_swap(
            asset_sender=swapper_account,
            asset_receiver=swap_creator,
            asset_close_to=swap_creator,
            asset_ids=[offered_asa_idx],
            swapper_funds_sender=swapper_account,
            swapper_funds_receiver=swap_creator,
            swapper_funds_close_to=swap_creator,
            proof_sender=swap_user,
            proof_receiver=swap_creator,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Close swap fails with wrong proof receiver")
        close_swap(
            asset_sender=swapper_account,
            asset_receiver=swap_creator,
            asset_close_to=swap_creator,
            asset_ids=[offered_asa_idx],
            swapper_funds_sender=swapper_account,
            swapper_funds_receiver=swap_creator,
            swapper_funds_close_to=swap_creator,
            proof_sender=swap_creator,
            proof_receiver=swap_user,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Close swap fails with wrong proof amount")
        close_swap(
            asset_sender=swapper_account,
            asset_receiver=swap_creator,
            asset_close_to=swap_creator,
            asset_ids=[offered_asa_idx],
            swapper_funds_sender=swapper_account,
            swapper_funds_receiver=swap_creator,
            swapper_funds_close_to=swap_creator,
            proof_sender=swap_creator,
            proof_receiver=swap_creator,
            proof_amt=1,
        )

    # Happy path
    close_swap(
        asset_sender=swapper_account,
        asset_receiver=swap_creator,
        asset_close_to=swap_creator,
        asset_ids=[offered_asa_idx],
        swapper_funds_sender=swapper_account,
        swapper_funds_receiver=swap_creator,
        swapper_funds_close_to=swap_creator,
        proof_sender=swap_creator,
        proof_receiver=swap_creator,
    )
