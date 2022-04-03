import pytest

from tests.auction.utils import (
    AUCTION_SELL_NFT_OPERATION,
    AUCTION_SET_PRICE_OPERATION,
    AuctionManager,
    assert_states,
)
from tests.common import fund_wallet, generate_wallet
from tests.common.utils import mint_asa
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
    main_account: Wallet,
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
    print("Up to here so far")

    #     accountAddress,
    #     escrowAddress,
    #     buyerAddress,
    #     appId,
    #     nftId,
    #     price,

    AuctionManager.sell_now(
        creator_account,
        escrow,
        fee_profits_a_account,
        fee_profits_a_account,
        buyer_account,
        app_id,
        auction_asa_id,
        0,
        AUCTION_SELL_NFT_OPERATION.FROM_WALLET,
    )

    # // Sell now with direct NFT transfer
    # contract.sellNow(master, thirdParty.address, {
    #     directTransfer: true,
    # });
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), new Uint8Array(32));
    # assert.equal(getGlobal(ASK_PRICE), 0);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 0);

    # // First ask offer
    # contract.setPrice(thirdParty, 10e6, {
    #     addNFT: true,
    # });
    # assert.deepEqual(
    # );
    # assert.equal(getGlobal(ASK_PRICE), 10e6);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.equal(getLocal(master.address, BID_PRICE), 0);

    # // Increase bid offer
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);
    # assert.equal(getLocal(master.address, BID_PRICE), 2e6);

    # // Buy now while increasing bid offer
    # console.log(
    #     contract.runtime.getGlobalState(
    #         ASK_PRICE
    # );
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), new Uint8Array(32));
    # assert.equal(getGlobal(ASK_PRICE), 0);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.equal(getLocal(master.address, BID_PRICE), 0);

    # // First ask offer
    # contract.setPrice(master, 10e6, {
    #     addNFT: true,
    # });
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), addressToPk(master.address));
    # assert.equal(getGlobal(ASK_PRICE), 10e6);

    # // Increase bid offer
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 2e6);

    # // Decrease ask offer
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), addressToPk(master.address));
    # assert.equal(getGlobal(ASK_PRICE), 5e6);

    # // Buy now while decreasing bid offer
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), new Uint8Array(32));
    # assert.equal(getGlobal(ASK_PRICE), 0);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 0);

    # // Create bid offer without ask offer
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 5e6);

    # // First ask offer
    # contract.setPrice(master, 10e6, {
    #     addNFT: true,
    # });
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), addressToPk(master.address));
    # assert.equal(getGlobal(ASK_PRICE), 10e6);
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 5e6);

    # // Sell now with direct NFT transfer
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), new Uint8Array(32));
    # assert.equal(getGlobal(ASK_PRICE), 0);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 0);
