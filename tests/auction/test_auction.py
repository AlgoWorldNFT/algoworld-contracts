import pytest

from tests.auction.utils import (
    AUCTION_SELL_NFT_OPERATION,
    AUCTION_SET_PRICE_OPERATION,
    AuctionManager,
    assert_states,
)
from tests.helpers import fund_wallet, generate_wallet
from tests.helpers.utils import mint_asa
from tests.models import (
    ALGOWORLD_APP_ARGS,
    AlgorandSandbox,
    GlobalStateConditional,
    LocalStateConditional,
    Wallet,
)

CONTRACTS_VERSION = "1"
EMPTY_WALLET_STATE = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"


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
    fund_wallet(funded_account, algorand_sandbox, initial_funds=int(100 * 1e6))
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


@pytest.fixture()
def auction_asa_id(creator_account: Wallet) -> int:
    return mint_asa(
        creator_account.public_key,
        creator_account.private_key,
        asset_name="Auction Card A",
        total=1,
        decimals=0,
    )


def test_auction_flow(
    creator_account: Wallet,
    buyer_account: Wallet,
    fee_profits_a_account: Wallet,
    fee_profits_b_account: Wallet,
    auction_asa_id: int,
):
    contract_tx, proxy, app_id = AuctionManager.create_contract(
        creator_account,
        fee_profits_a_account,
        fee_profits_b_account,
        CONTRACTS_VERSION,
        auction_asa_id,
    )
    assert contract_tx and proxy and app_id
    AuctionManager.opt_in_wallet(creator_account, app_id)

    # Check if initial global state BEFORE configuration, are set to correct default values
    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ESCROW_ADDRESS,
                arg_value=app_id,
                expected_value=EMPTY_WALLET_STATE,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=EMPTY_WALLET_STATE,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.CREATOR_ADDRESS,
                arg_value=app_id,
                expected_value=creator_account.public_key,
            ),
        ]
    )

    configure_tx, escrow = AuctionManager.configure_contract(
        creator_account,
        fee_profits_a_account,
        fee_profits_b_account,
        auction_asa_id,
        app_id,
    )
    assert configure_tx and escrow

    # Check if initial global state AFTER configuration, are set to correct default values

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ESCROW_ADDRESS,
                arg_value=app_id,
                expected_value=escrow.public_key,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=EMPTY_WALLET_STATE,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.CREATOR_ADDRESS,
                arg_value=app_id,
                expected_value=creator_account.public_key,
            ),
        ]
    )

    # Set first ask offer
    AuctionManager.set_price(
        creator=creator_account,
        escrow=escrow,
        app_id=app_id,
        asset_id=auction_asa_id,
        price=1_000_000,
        operation=AUCTION_SET_PRICE_OPERATION.ADD_NFT,
    )

    # At this point we have 0 bids, 1 ask price, 1 creator
    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=creator_account.public_key,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=1_000_000,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=0,
            ),
        ]
    )

    # Update ask offer
    AuctionManager.set_price(
        creator=creator_account,
        escrow=escrow,
        app_id=app_id,
        asset_id=auction_asa_id,
        price=10_000_000,
        operation=AUCTION_SET_PRICE_OPERATION.DEFAULT_CALL,
    )

    # Ask price value should be equal to 10e6 now
    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=creator_account.public_key,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=10_000_000,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=0,
            ),
        ]
    )

    # First bid offer
    AuctionManager.opt_in_wallet(buyer_account, app_id)
    AuctionManager.opt_in_asa(buyer_account, auction_asa_id)
    assert_states(
        [
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID_PRICE,
                account=buyer_account,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=0,
            ),
        ]
    )
    AuctionManager.bid_auction(buyer_account, escrow, app_id, 5_000_000)
    assert_states(
        [
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID_PRICE,
                account=buyer_account,
                arg_value=app_id,
                expected_value=5_000_000,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=1,
            ),
        ]
    )

    # Second bid - increase
    AuctionManager.bid_auction(buyer_account, escrow, app_id, 6_000_000)
    assert_states(
        [
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID_PRICE,
                account=buyer_account,
                arg_value=app_id,
                expected_value=6_000_000,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=1,
            ),
        ]
    )

    # Third bid - decrease
    AuctionManager.bid_auction(buyer_account, escrow, app_id, 4_000_000)
    assert_states(
        [
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID_PRICE,
                account=buyer_account,
                arg_value=app_id,
                expected_value=4_000_000,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=1,
            ),
        ]
    )

    # Remove ask offer and withdraw NFT
    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=creator_account.public_key,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=10_000_000,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=1,
            ),
        ]
    )

    AuctionManager.set_price(
        creator_account,
        escrow,
        app_id,
        auction_asa_id,
        0,
        AUCTION_SET_PRICE_OPERATION.REMOVE_NFT,
    )

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=EMPTY_WALLET_STATE,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=1,
            ),
        ]
    )

    AuctionManager.sell_now(
        creator_account,
        escrow,
        fee_profits_a_account,
        fee_profits_b_account,
        buyer_account,
        app_id,
        auction_asa_id,
        AUCTION_SELL_NFT_OPERATION.FROM_WALLET,
    )

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=EMPTY_WALLET_STATE,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=0,
            ),
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID_PRICE,
                arg_value=app_id,
                account=buyer_account,
                expected_value=0,
            ),
        ]
    )

    # // First ask offer

    AuctionManager.set_price(
        buyer_account,
        escrow,
        app_id,
        auction_asa_id,
        10_000_000,
        AUCTION_SET_PRICE_OPERATION.ADD_NFT,
    )

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=buyer_account.public_key,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=10_000_000,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=0,
            ),
        ]
    )

    AuctionManager.bid_auction(creator_account, escrow, app_id, 2_000_000)

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=1,
            ),
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID_PRICE,
                arg_value=app_id,
                account=creator_account,
                expected_value=2_000_000,
            ),
        ]
    )

    #   // Buy now while increasing bid offer
    AuctionManager.buy_now(
        creator_account,
        escrow,
        fee_profits_a_account,
        fee_profits_b_account,
        buyer_account,
        app_id,
        auction_asa_id,
    )

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=EMPTY_WALLET_STATE,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=0,
            ),
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID_PRICE,
                arg_value=app_id,
                account=creator_account,
                expected_value=0,
            ),
        ]
    )

    # Set new price
    AuctionManager.set_price(
        creator_account,
        escrow,
        app_id,
        auction_asa_id,
        10_000_000,
        AUCTION_SET_PRICE_OPERATION.ADD_NFT,
    )

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=creator_account.public_key,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=10_000_000,
            ),
        ]
    )

    # Bid while increasing bid offer
    AuctionManager.bid_auction(buyer_account, escrow, app_id, 2_000_000)

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID,
                arg_value=app_id,
                expected_value=1,
            ),
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID,
                arg_value=app_id,
                account=buyer_account,
                expected_value=2_000_000,
            ),
        ]
    )

    # Decrease price without nft transfer
    AuctionManager.set_price(
        creator_account,
        escrow,
        app_id,
        auction_asa_id,
        5_000_000,
        AUCTION_SET_PRICE_OPERATION.DEFAULT_CALL,
    )

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=creator_account.public_key,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=5_000_000,
            ),
        ]
    )

    # Buy while decreasing bid offer
    AuctionManager.buy_now(
        buyer_account,
        escrow,
        fee_profits_a_account,
        fee_profits_b_account,
        creator_account,
        app_id,
        auction_asa_id,
    )

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=EMPTY_WALLET_STATE,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=0,
            ),
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID_PRICE,
                arg_value=app_id,
                account=buyer_account,
                expected_value=0,
            ),
        ]
    )

    # Bid without asking offer
    AuctionManager.bid_auction(creator_account, escrow, app_id, 5_000_000)
    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID,
                arg_value=app_id,
                expected_value=1,
            ),
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID,
                arg_value=app_id,
                account=creator_account,
                expected_value=5_000_000,
            ),
        ]
    )

    AuctionManager.set_price(
        buyer_account,
        escrow,
        app_id,
        auction_asa_id,
        10_000_000,
        AUCTION_SET_PRICE_OPERATION.ADD_NFT,
    )
    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=buyer_account.public_key,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID,
                arg_value=app_id,
                expected_value=1,
            ),
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID,
                arg_value=app_id,
                account=creator_account,
                expected_value=5_000_000,
            ),
        ]
    )

    AuctionManager.sell_now(
        buyer_account,
        escrow,
        fee_profits_a_account,
        fee_profits_b_account,
        creator_account,
        app_id,
        auction_asa_id,
        AUCTION_SELL_NFT_OPERATION.FROM_ESCROW,
    )

    assert_states(
        [
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.OWNER_ADDRESS,
                arg_value=app_id,
                expected_value=EMPTY_WALLET_STATE,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.ASK_PRICE,
                arg_value=app_id,
                expected_value=0,
            ),
            GlobalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BIDS_AMOUNT,
                arg_value=app_id,
                expected_value=0,
            ),
            LocalStateConditional(
                arg_name=ALGOWORLD_APP_ARGS.BID_PRICE,
                arg_value=app_id,
                account=creator_account,
                expected_value=0,
            ),
        ]
    )
