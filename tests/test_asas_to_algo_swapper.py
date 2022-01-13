import pytest
from algosdk.error import AlgodHTTPError

from src.asas_to_algo_swapper import BASE_OPTIN_FUNDING_AMOUNT
from tests.common import (
    INCENTIVE_FEE_ADDRESS,
    AsasToAlgoSwapConfig,
    asa_to_algo_swap,
    close_swap,
    fund_wallet,
    generate_random_offered_asas,
    generate_swapper,
    generate_wallet,
    mint_asa,
    opt_in_asa,
    swapper_deposit,
    swapper_opt_in,
)
from tests.models import LogicSigWallet, Wallet

#### Fixtures


@pytest.fixture()
def swap_creator() -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account)
    print(f"\n --- Swapper Creator {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def swap_user() -> Wallet:
    funded_account = generate_wallet()
    fund_wallet(funded_account)
    print(f"\n --- Swapper User {funded_account.public_key} funded.")
    return funded_account


@pytest.fixture()
def incentive_wallet() -> Wallet:
    incentive_account = Wallet("", INCENTIVE_FEE_ADDRESS)
    fund_wallet(incentive_account)
    print(f"\n --- Incentive Wallet {incentive_account.public_key} funded.")
    return incentive_account


@pytest.fixture()
def offered_asa_a_idx(swap_creator: Wallet) -> int:
    return mint_asa(
        swap_creator.public_key,
        swap_creator.private_key,
        asset_name="Card A",
        total=1,
        decimals=0,
    )


@pytest.fixture()
def offered_asa_b_idx(swap_creator: Wallet) -> int:
    return mint_asa(
        swap_creator.public_key,
        swap_creator.private_key,
        asset_name="Card B",
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
    swap_creator: Wallet, offered_asa_a_idx: int, offered_asa_b_idx: int
) -> LogicSigWallet:

    return generate_swapper(
        AsasToAlgoSwapConfig(
            swap_creator=swap_creator.public_key,
            offered_asa_amounts={str(offered_asa_a_idx): 1, str(offered_asa_b_idx): 1},
            requested_algo_amount=1_000_000,
            max_fee=1_000,
            optin_funding_amount=BASE_OPTIN_FUNDING_AMOUNT * 2,
            incentive_fee_address="RJVRGSPGSPOG7W3V7IMZZ2BAYCABW3YC5MWGKEOPAEEI5ZK5J2GSF6Y26A",
            incentive_fee_amount=10_000,
        )
    )


#### Tests


def test_multi_asa_optin(
    swapper_account: LogicSigWallet,
    swap_creator: Wallet,
    swap_user: Wallet,
    offered_asa_a_idx: int,
    offered_asa_b_idx: int,
    other_asa_idx: int,
):

    with pytest.raises(AlgodHTTPError):
        print("\n --- Opt-In fails if not executed by swap creator")
        swapper_opt_in(
            swap_creator=swap_user,
            swapper_account=swapper_account,
            assets={offered_asa_a_idx: 0, offered_asa_b_idx: 0},
            funding_amount=BASE_OPTIN_FUNDING_AMOUNT * 2,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Opt-In fails with wrong funding amount")
        swapper_opt_in(
            swap_creator=swap_creator,
            swapper_account=swapper_account,
            assets={offered_asa_a_idx: 0, offered_asa_b_idx: 0},
            funding_amount=BASE_OPTIN_FUNDING_AMOUNT - 2,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Opt-In fails with wrong ASA")
        swapper_opt_in(
            swap_creator=swap_creator,
            swapper_account=swapper_account,
            assets={other_asa_idx: 0, other_asa_idx: 0},
            funding_amount=BASE_OPTIN_FUNDING_AMOUNT * 2,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Opt-In fails with wrong ASA amount")
        swapper_opt_in(
            swap_creator=swap_creator,
            swapper_account=swapper_account,
            assets={offered_asa_a_idx: 1, offered_asa_b_idx: 1},
            funding_amount=BASE_OPTIN_FUNDING_AMOUNT * 2,
        )

    # Happy path
    swapper_opt_in(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_a_idx: 0, offered_asa_b_idx: 0},
        funding_amount=BASE_OPTIN_FUNDING_AMOUNT * 2,
    )


def test_swapper_asa_swap(
    swapper_account: LogicSigWallet,
    swap_creator: Wallet,
    swap_user: Wallet,
    incentive_wallet: Wallet,
    offered_asa_a_idx: int,
    offered_asa_b_idx: int,
):
    opt_in_asa(swap_user, [offered_asa_a_idx, offered_asa_b_idx])

    swapper_opt_in(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_a_idx: 0, offered_asa_b_idx: 0},
        funding_amount=BASE_OPTIN_FUNDING_AMOUNT * 2,
    )

    swapper_deposit(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_a_idx: 1, offered_asa_b_idx: 1},
    )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong requested algo amount")
        asa_to_algo_swap(
            offered_assets_sender=swapper_account,
            offered_assets_receiver=swap_user,
            offered_assets={offered_asa_a_idx: 1, offered_asa_b_idx: 1},
            requested_algo_amount=10_000_000,
            requested_algo_sender=swap_user,
            requested_algo_receiver=swap_creator,
            incentive_wallet=incentive_wallet,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong offered ASA ids order")
        asa_to_algo_swap(
            offered_assets_sender=swapper_account,
            offered_assets_receiver=swap_user,
            offered_assets={offered_asa_b_idx: 1, offered_asa_a_idx: 1},
            requested_algo_amount=1_000_000,
            requested_algo_sender=swap_user,
            requested_algo_receiver=swap_creator,
            incentive_wallet=incentive_wallet,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong offered ASA ids")
        asa_to_algo_swap(
            offered_assets_sender=swapper_account,
            offered_assets_receiver=swap_user,
            offered_assets={123: 1, 321: 1},
            requested_algo_amount=1_000_000,
            requested_algo_sender=swap_user,
            requested_algo_receiver=swap_creator,
            incentive_wallet=incentive_wallet,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong requested asset receiver")
        asa_to_algo_swap(
            offered_assets_sender=swapper_account,
            offered_assets_receiver=swap_user,
            offered_assets={offered_asa_a_idx: 1, offered_asa_b_idx: 1},
            requested_algo_amount=1_000_000,
            requested_algo_sender=swap_user,
            requested_algo_receiver=swap_user,
            incentive_wallet=incentive_wallet,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong incentive algo receiver")
        asa_to_algo_swap(
            offered_assets_sender=swapper_account,
            offered_assets_receiver=swap_user,
            offered_assets={offered_asa_a_idx: 1, offered_asa_b_idx: 1},
            requested_algo_amount=1_000_000,
            requested_algo_sender=swap_user,
            requested_algo_receiver=swap_user,
            incentive_wallet=swap_user,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong incentive algo amount")
        asa_to_algo_swap(
            offered_assets_sender=swapper_account,
            offered_assets_receiver=swap_user,
            offered_assets={offered_asa_a_idx: 1, offered_asa_b_idx: 1},
            requested_algo_amount=1_000_000,
            requested_algo_sender=swap_user,
            requested_algo_receiver=swap_creator,
            incentive_wallet=incentive_wallet,
            incentive_amount=200,
        )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Swap fails with wrong incentive algo sener")
        asa_to_algo_swap(
            offered_assets_sender=swapper_account,
            offered_assets_receiver=swap_user,
            offered_assets={offered_asa_a_idx: 1, offered_asa_b_idx: 1},
            requested_algo_amount=1_000_000,
            requested_algo_sender=swapper_account,
            requested_algo_receiver=swap_creator,
            incentive_wallet=incentive_wallet,
        )

    # Happy path
    asa_to_algo_swap(
        offered_assets_sender=swapper_account,
        offered_assets_receiver=swap_user,
        offered_assets={offered_asa_a_idx: 1, offered_asa_b_idx: 1},
        requested_algo_amount=1_000_000,
        requested_algo_sender=swap_user,
        requested_algo_receiver=swap_creator,
        incentive_wallet=incentive_wallet,
    )


def test_swapper_random_asas_swap(
    swap_creator: Wallet, swap_user: Wallet, incentive_wallet: Wallet
):
    """Randomly generates 5 ASAs of different digits and unit amounts. And attempts a multi asa swap.
    """

    random_offered_asas = generate_random_offered_asas(swap_creator)
    asa_ids = [asa["id"] for asa in random_offered_asas]
    offered_asas_opt_ins = {}
    offered_asas = {}
    incentive_fee = 10_000
    requested_algo_amount = 1_000_000

    for asa in random_offered_asas:
        asa_id = asa["id"]
        offered_asas[asa_id] = asa["amount"] // 2  # send half of offered asas available
        offered_asas_opt_ins[asa_id] = 0

    swapper_account = generate_swapper(
        AsasToAlgoSwapConfig(
            swap_creator=swap_creator.public_key,
            offered_asa_amounts=offered_asas,
            requested_algo_amount=requested_algo_amount,
            max_fee=1_000,
            optin_funding_amount=BASE_OPTIN_FUNDING_AMOUNT * len(offered_asas),
            incentive_fee_address=incentive_wallet.public_key,
            incentive_fee_amount=incentive_fee,
        )
    )

    opt_in_asa(swap_user, asa_ids)

    swapper_opt_in(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets=offered_asas_opt_ins,
        funding_amount=BASE_OPTIN_FUNDING_AMOUNT * len(offered_asas),
    )

    swapper_deposit(
        swap_creator=swap_creator, swapper_account=swapper_account, assets=offered_asas
    )

    # Happy path
    asa_to_algo_swap(
        offered_assets_sender=swapper_account,
        offered_assets_receiver=swap_user,
        offered_assets=offered_asas,
        requested_algo_amount=requested_algo_amount,
        requested_algo_sender=swap_user,
        requested_algo_receiver=swap_creator,
        incentive_wallet=incentive_wallet,
    )


def test_swapper_close_swap(
    swapper_account: LogicSigWallet,
    swap_creator: Wallet,
    swap_user: Wallet,
    offered_asa_a_idx: int,
    offered_asa_b_idx: int,
    other_asa_idx: int,
):
    opt_in_asa(swap_creator, [other_asa_idx])
    opt_in_asa(swap_user, [offered_asa_a_idx, offered_asa_b_idx])

    swapper_opt_in(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_a_idx: 0, offered_asa_b_idx: 0},
        funding_amount=BASE_OPTIN_FUNDING_AMOUNT * 2,
    )

    swapper_deposit(
        swap_creator=swap_creator,
        swapper_account=swapper_account,
        assets={offered_asa_a_idx: 1, offered_asa_b_idx: 1},
    )

    with pytest.raises(AlgodHTTPError):
        print("\n --- Close swap fails with wrong asset receiver")
        close_swap(
            asset_sender=swapper_account,
            asset_receiver=swap_user,
            asset_close_to=swap_creator,
            asset_ids=[offered_asa_a_idx, offered_asa_b_idx],
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
            asset_ids=[offered_asa_a_idx, offered_asa_b_idx],
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
            asset_ids=[offered_asa_a_idx, offered_asa_b_idx],
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
            asset_ids=[offered_asa_a_idx, offered_asa_b_idx],
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
            asset_ids=[offered_asa_a_idx, offered_asa_b_idx],
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
            asset_ids=[offered_asa_a_idx, offered_asa_b_idx],
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
            asset_ids=[offered_asa_a_idx, offered_asa_b_idx],
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
        asset_ids=[offered_asa_a_idx, offered_asa_b_idx],
        swapper_funds_sender=swapper_account,
        swapper_funds_receiver=swap_creator,
        swapper_funds_close_to=swap_creator,
        proof_sender=swap_creator,
        proof_receiver=swap_creator,
    )
