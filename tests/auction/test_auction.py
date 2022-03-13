import pytest

from tests.auction.utils import ALGOWORLD_APP_ARGS, AuctionManager, get_global_state
from tests.common import fund_wallet, generate_wallet
from tests.common.utils import mint_asa
from tests.models import AlgorandSandbox, Wallet

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

    configure_tx, escrow = AuctionManager.configure_contract(
        creator_account,
        fee_profits_a_account,
        fee_profits_b_account,
        auction_asa_id,
        app_id,
    )
    assert configure_tx and escrow

    # Check if initial global state are set to correct default values
    assert get_global_state(ALGOWORLD_APP_ARGS.ASK_PRICE, app_id) == 0
    assert get_global_state(ALGOWORLD_APP_ARGS.BIDS_AMOUNT, app_id) == 0
    assert (
        get_global_state(ALGOWORLD_APP_ARGS.ESCROW_ADDRESS, app_id) == escrow.public_key
    )
    assert (
        get_global_state(ALGOWORLD_APP_ARGS.CREATOR_ADDRESS, app_id)
        == creator_account.public_key
    )
    assert (
        get_global_state(ALGOWORLD_APP_ARGS.OWNER_ADDRESS, app_id) == EMPTY_WALLET_STATE
    )

    # // Setup application

    # assert.isDefined(contract.getApplicationId());
    # assert.equal(getGlobal(ASK_PRICE), 0);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), new Uint8Array(32));
    # assert.deepEqual(getGlobal(ESCROW_ADDRESS), new Uint8Array(32));
    # assert.deepEqual(getGlobal(CREATOR_ADDRESS), creatorPk);

    # // Setup escrow account

    # // Verify escrow storage
    # assert.deepEqual(getGlobal(ESCROW_ADDRESS), addressToPk(contract.getEscrowAddress()));

    # // Opt-in

    # // First ask offer
    # contract.setPrice(master, 1e6, {
    # });

    # assert.deepEqual(getGlobal(OWNER_ADDRESS), addressToPk(master.address));
    # assert.equal(getGlobal(ASK_PRICE), 1e6);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);

    # // Update ask offer
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), addressToPk(master.address));
    # assert.equal(getGlobal(ASK_PRICE), 10e6);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);

    # // First bid offer
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 0);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 5e6);
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);

    # // Increase bid offer
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 6e6);
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);

    # // Decrease bid offer
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 4e6);
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);

    # // Remove ask offer and withdraw NFT
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), addressToPk(master.address));
    # assert.equal(getGlobal(ASK_PRICE), 10e6);
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);
    # contract.setPrice(master, 0, {
    # });
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), new Uint8Array(32));
    # assert.equal(getGlobal(ASK_PRICE), 0);
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);

    # // Sell now with direct NFT transfer
    # contract.sellNow(master, thirdParty.address, {
    # });
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), new Uint8Array(32));
    # assert.equal(getGlobal(ASK_PRICE), 0);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.equal(getLocal(thirdParty.address, BID_PRICE), 0);

    # // First ask offer
    # contract.setPrice(thirdParty, 10e6, {
    # });
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), addressToPk(thirdParty.address));
    # assert.equal(getGlobal(ASK_PRICE), 10e6);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.equal(getLocal(master.address, BID_PRICE), 0);

    # // Increase bid offer
    # assert.equal(getGlobal(BIDS_AMOUNT), 1);
    # assert.equal(getLocal(master.address, BID_PRICE), 2e6);

    # // Buy now while increasing bid offer
    # assert.deepEqual(getGlobal(OWNER_ADDRESS), new Uint8Array(32));
    # assert.equal(getGlobal(ASK_PRICE), 0);
    # assert.equal(getGlobal(BIDS_AMOUNT), 0);
    # assert.equal(getLocal(master.address, BID_PRICE), 0);

    # // First ask offer
    # contract.setPrice(master, 10e6, {
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

    assert True
