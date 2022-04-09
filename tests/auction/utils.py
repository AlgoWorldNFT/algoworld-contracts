import base64
from random import randint

from algosdk.encoding import encode_address
from algosdk.future.transaction import (
    ApplicationCallTxn,
    ApplicationCreateTxn,
    ApplicationOptInTxn,
    AssetOptInTxn,
    AssetTransferTxn,
    OnComplete,
    PaymentTxn,
    StateSchema,
)

from src.contracts import (
    get_clear_teal,
    get_escrow_teal,
    get_manager_teal,
    get_proxy_teal,
)
from tests.common.utils import (
    _algod_client,
    _indexer_client,
    group_sign_send_wait,
    logic_signature,
)
from tests.models import (
    ALGOWORLD_APP_ARGS,
    LocalStateConditional,
    LogicSigWallet,
    Wallet,
)

ALGOD = _algod_client()
INDEXER = _indexer_client()
CONTRACT_CREATION_FEE = 466_000
CONTRACT_CONFIG_FEE = 302_000


def decode_global_state(state):
    decoded_state = {}
    for obj in state:
        key = base64.b64decode(obj["key"]).decode("utf-8")
        value_type = obj["value"]["type"]
        if value_type == 2:
            decoded_state[key] = int(obj["value"]["uint"])
        elif value_type == 1:
            decoded_state[key] = encode_address(base64.b64decode(obj["value"]["bytes"]))
    return decoded_state


def decode_local_state(state):
    decoded_state = {}
    local_state_kv = state["key-value"]
    for obj in local_state_kv:
        key = base64.b64decode(obj["key"]).decode("utf-8")
        value_type = obj["value"]["type"]
        if value_type == 2:
            decoded_state[key] = int(obj["value"]["uint"])
        elif value_type == 1:
            decoded_state[key] = encode_address(base64.b64decode(obj["value"]["bytes"]))
    return decoded_state


def get_global_state(app_arg: ALGOWORLD_APP_ARGS, app_id: int):
    global_state = ALGOD.application_info(app_id)["params"]["global-state"]
    decoded_global_state = decode_global_state(global_state)
    return decoded_global_state[app_arg.decode()]


def assert_states(conditionals: list):
    for condition in conditionals:
        if isinstance(condition, LocalStateConditional):
            assert (
                get_local_state(
                    condition.account, condition.arg_name, condition.arg_value
                )
                == condition.expected_value
            )
        else:
            assert (
                get_global_state(condition.arg_name, condition.arg_value)
                == condition.expected_value
            )


def get_local_state(account: Wallet, app_arg: ALGOWORLD_APP_ARGS, app_id: int):

    account_info = ALGOD.account_info(account.public_key)

    if "apps-local-state" in account_info:
        account_local_state = None
        for local_state in account_info["apps-local-state"]:
            if local_state["id"] == app_id:
                account_local_state = local_state
                break
        if account_local_state:
            return decode_local_state(account_local_state)[app_arg.decode()]

    return None


class AUCTION_SET_PRICE_OPERATION:
    ADD_NFT: int = 1
    REMOVE_NFT: int = 2
    DEFAULT_CALL: int = 3


class AUCTION_SELL_NFT_OPERATION:
    FROM_ESCROW: int = 1
    FROM_WALLET: int = 2


class AuctionManager:
    @staticmethod
    def create_proxy():
        proxy_id = randint(1, 2147483647)
        proxy_teal = get_proxy_teal(proxy_id)
        proxy_lsig = logic_signature(proxy_teal)
        return LogicSigWallet(logicsig=proxy_lsig, public_key=proxy_lsig.address())

    @staticmethod
    def create_manager(
        fee_address_a: Wallet, fee_address_b: Wallet, contract_version: str
    ):
        manager_teal = get_manager_teal(
            fee_address_a=fee_address_a.public_key,
            fee_address_b=fee_address_b.public_key,
            contract_version=contract_version,
        )
        manager_compiled = ALGOD.compile(manager_teal)
        manager_params = {
            "num_local_ints": 1,
            "num_local_byte_slices": 0,
            "num_global_ints": 4,
            "num_global_byte_slices": 3,
        }
        return base64.b64decode(manager_compiled["result"]), manager_params

    @staticmethod
    def create_clear():
        clear_teal = get_clear_teal()
        response = ALGOD.compile(clear_teal)
        return base64.b64decode(response["result"])

    @staticmethod
    def create_escrow(
        app_id: int, asa_id: int, fee_address_a: Wallet, fee_address_b: Wallet
    ):
        escrow_teal = get_escrow_teal(
            app_id,
            asa_id,
            fee_address_a=fee_address_a.public_key,
            fee_address_b=fee_address_b.public_key,
        )
        escrow_lsig = logic_signature(escrow_teal)
        return LogicSigWallet(logicsig=escrow_lsig, public_key=escrow_lsig.address())

    @staticmethod
    def create_contract(
        creator_address: Wallet,
        fee_address_a: Wallet,
        fee_address_b: Wallet,
        contracts_version: str,
        asa_id: int,
    ):

        proxy = AuctionManager.create_proxy()

        manager_compiled, manager_params = AuctionManager.create_manager(
            fee_address_a=fee_address_a,
            fee_address_b=fee_address_b,
            contract_version=contracts_version,
        )

        clear_compiled = AuctionManager.create_clear()
        fee_tx = PaymentTxn(
            creator_address.public_key,
            ALGOD.suggested_params(),
            proxy.public_key,
            CONTRACT_CREATION_FEE,
            None,
            "I am a fee transaction for reating algoworld contract",
        )

        app_create_tx = ApplicationCreateTxn(
            sender=proxy.public_key,
            sp=ALGOD.suggested_params(),
            on_complete=OnComplete.NoOpOC,
            approval_program=manager_compiled,
            clear_program=clear_compiled,
            global_schema=StateSchema(
                manager_params["num_global_ints"],
                manager_params["num_global_byte_slices"],
            ),
            local_schema=StateSchema(
                manager_params["num_local_ints"],
                manager_params["num_local_byte_slices"],
            ),
            app_args=[asa_id],
            accounts=[creator_address.public_key],
        )

        tx = group_sign_send_wait([creator_address, proxy], [fee_tx, app_create_tx])
        app_id = ALGOD.account_info(proxy.public_key)["created-apps"][0]["id"]

        return tx, proxy, app_id

    @staticmethod
    def configure_contract(
        creator_address: Wallet,
        fee_address_a: Wallet,
        fee_address_b: Wallet,
        asa_id: int,
        app_id: int,
    ):
        escrow = AuctionManager.create_escrow(
            app_id, asa_id, fee_address_a, fee_address_b
        )
        fee_tx = PaymentTxn(
            creator_address.public_key,
            ALGOD.suggested_params(),
            escrow.public_key,
            CONTRACT_CONFIG_FEE,
            None,
            "",
        )

        config_tx = ApplicationCallTxn(
            sender=creator_address.public_key,
            sp=ALGOD.suggested_params(),
            index=app_id,
            on_complete=OnComplete.NoOpOC,
            app_args=[ALGOWORLD_APP_ARGS.CONFIGURE],
            accounts=[escrow.public_key],
            note="",
        )

        asa_transfer_tx = AssetOptInTxn(
            sender=escrow.public_key,
            sp=ALGOD.suggested_params(),
            index=asa_id,
        )

        tx = group_sign_send_wait(
            [creator_address, creator_address, escrow],
            [config_tx, fee_tx, asa_transfer_tx],
        )

        return tx, escrow

    @staticmethod
    def set_price(
        creator: Wallet,
        escrow: Wallet,
        app_id: int,
        asset_id: int,
        price: int,
        operation: AUCTION_SET_PRICE_OPERATION,
    ):
        app_args = [ALGOWORLD_APP_ARGS.SET_PRICE, price]
        txn_group = []
        signers = []
        if operation == AUCTION_SET_PRICE_OPERATION.ADD_NFT:
            txn_group.extend(
                [
                    ApplicationCallTxn(
                        sender=creator.public_key,
                        sp=ALGOD.suggested_params(),
                        index=app_id,
                        on_complete=OnComplete.NoOpOC,
                        app_args=app_args,
                        note="",
                    ),
                    AssetTransferTxn(
                        sender=creator.public_key,
                        sp=ALGOD.suggested_params(),
                        receiver=escrow.public_key,
                        index=asset_id,
                        amt=1,
                    ),
                ]
            )
            signers.extend([creator, creator])
        elif operation == AUCTION_SET_PRICE_OPERATION.REMOVE_NFT:
            txn_group.extend(
                [
                    ApplicationCallTxn(
                        sender=creator.public_key,
                        sp=ALGOD.suggested_params(),
                        index=app_id,
                        on_complete=OnComplete.NoOpOC,
                        app_args=app_args,
                        note="",
                    ),
                    PaymentTxn(
                        creator.public_key,
                        ALGOD.suggested_params(),
                        escrow.public_key,
                        1000,
                        None,
                        "I am a fee transaction for setting offer on algoworld contract",
                    ),
                    AssetTransferTxn(
                        sender=escrow.public_key,
                        sp=ALGOD.suggested_params(),
                        receiver=creator.public_key,
                        index=asset_id,
                        amt=1,
                    ),
                ]
            )
            signers.extend([creator, creator, escrow])
        else:
            txn_group = [
                ApplicationCallTxn(
                    sender=creator.public_key,
                    sp=ALGOD.suggested_params(),
                    index=app_id,
                    on_complete=OnComplete.NoOpOC,
                    app_args=app_args,
                    note="",
                )
            ]
            signers = [creator]

        tx = group_sign_send_wait(signers, txn_group)
        return tx

    @staticmethod
    def opt_in_wallet(wallet: Wallet, app_id: int):

        app_opt_in = ApplicationOptInTxn(
            sender=wallet.public_key,
            sp=ALGOD.suggested_params(),
            index=app_id,
        )

        tx = group_sign_send_wait([wallet], [app_opt_in])
        return tx

    @staticmethod
    def opt_in_asa(wallet: Wallet, asa_id: int):

        app_opt_in = AssetOptInTxn(
            sender=wallet.public_key,
            sp=ALGOD.suggested_params(),
            index=asa_id,
        )

        tx = group_sign_send_wait([wallet], [app_opt_in])
        return tx

    @staticmethod
    def bid_auction(wallet: Wallet, escrow: Wallet, app_id: int, bid_price: int):
        current_price = get_local_state(wallet, ALGOWORLD_APP_ARGS.BID_PRICE, app_id)
        current_price = 0 if current_price is None else current_price

        price_difference = bid_price - current_price
        app_args = [ALGOWORLD_APP_ARGS.BID]

        tx_group = []
        signers = []

        if price_difference >= 0:
            tx_group = [
                ApplicationCallTxn(
                    sender=wallet.public_key,
                    sp=ALGOD.suggested_params(),
                    index=app_id,
                    on_complete=OnComplete.NoOpOC,
                    app_args=app_args,
                ),
                PaymentTxn(
                    sender=wallet.public_key,
                    sp=ALGOD.suggested_params(),
                    receiver=escrow.public_key,
                    amt=price_difference,
                    close_remainder_to=None,
                ),
            ]
            signers = [wallet, wallet]
        else:
            tx_group = [
                ApplicationCallTxn(
                    sender=wallet.public_key,
                    sp=ALGOD.suggested_params(),
                    index=app_id,
                    on_complete=OnComplete.NoOpOC,
                    app_args=app_args,
                ),
                PaymentTxn(
                    wallet.public_key,
                    ALGOD.suggested_params(),
                    escrow.public_key,
                    1_000,
                    None,
                ),
                PaymentTxn(
                    escrow.public_key,
                    ALGOD.suggested_params(),
                    wallet.public_key,
                    int(abs(price_difference)),
                    None,
                ),
            ]
            signers = [wallet, wallet, escrow]

        tx = group_sign_send_wait(signers, tx_group)
        return tx

    @staticmethod
    def sell_now(
        account_address: Wallet,
        escrow_address: LogicSigWallet,
        fee_1_address: Wallet,
        fee_2_address: Wallet,
        buyer_address: Wallet,
        app_id: int,
        nft_id: int,
        operation_type: AUCTION_SET_PRICE_OPERATION,
    ):

        price = get_local_state(buyer_address, ALGOWORLD_APP_ARGS.BID_PRICE, app_id)
        price = 0 if price is None else price

        fee = (price * 5) // 100
        suggested_params = ALGOD.suggested_params()
        price_with_fee = price - fee

        signers = [
            account_address,
            account_address,
            escrow_address,
            escrow_address
            if operation_type == AUCTION_SELL_NFT_OPERATION.FROM_ESCROW
            else account_address,
            escrow_address,
            escrow_address,
        ]
        tx_group = [
            ApplicationCallTxn(
                sender=account_address.public_key,
                sp=suggested_params,
                index=app_id,
                on_complete=OnComplete.NoOpOC,
                accounts=[buyer_address.public_key],
                app_args=[ALGOWORLD_APP_ARGS.SELL_NOW],
                note="",
            ),
            PaymentTxn(
                account_address.public_key,
                suggested_params,
                escrow_address.public_key,
                int(suggested_params.min_fee) * 4
                if operation_type == AUCTION_SELL_NFT_OPERATION.FROM_ESCROW
                else int(suggested_params.min_fee * 3),
            ),
            PaymentTxn(
                escrow_address.public_key,
                suggested_params,
                account_address.public_key,
                int(price_with_fee),
            ),
            AssetTransferTxn(
                sender=escrow_address.public_key,
                sp=suggested_params,
                receiver=buyer_address.public_key,
                index=nft_id,
                amt=1,
            )
            if operation_type == AUCTION_SELL_NFT_OPERATION.FROM_ESCROW
            else AssetTransferTxn(
                sender=account_address.public_key,
                sp=suggested_params,
                receiver=buyer_address.public_key,
                index=nft_id,
                amt=1,
            ),
            PaymentTxn(
                escrow_address.public_key,
                suggested_params,
                fee_1_address.public_key,
                int(fee // 2),
            ),
            PaymentTxn(
                escrow_address.public_key,
                suggested_params,
                fee_2_address.public_key,
                int(fee // 2),
            ),
        ]

        tx = group_sign_send_wait(signers, tx_group)
        return tx

    @staticmethod
    def buy_now(
        account_address: Wallet,
        escrow_address: LogicSigWallet,
        fee_1_address: Wallet,
        fee_2_address: Wallet,
        seller_address: Wallet,
        app_id: int,
        nft_id: int,
    ):

        user_bid_price = get_local_state(
            account_address, ALGOWORLD_APP_ARGS.BID_PRICE, app_id
        )
        user_bid_price = 0 if user_bid_price is None else user_bid_price
        price = get_global_state(ALGOWORLD_APP_ARGS.ASK_PRICE, app_id)
        price_diff = price - user_bid_price
        fee = (price * 5) // 100
        suggested_params = ALGOD.suggested_params()
        price_with_fee = price - fee

        tx_group = []
        signers = []
        if price_diff >= 0:
            tx_group = [
                ApplicationCallTxn(
                    sender=account_address.public_key,
                    sp=suggested_params,
                    index=app_id,
                    on_complete=OnComplete.NoOpOC,
                    app_args=[ALGOWORLD_APP_ARGS.BUY_NOW],
                ),
                PaymentTxn(
                    sender=account_address.public_key,
                    sp=suggested_params,
                    receiver=escrow_address.public_key,
                    amt=suggested_params.min_fee * 4,
                ),
                PaymentTxn(
                    sender=account_address.public_key,
                    sp=suggested_params,
                    receiver=escrow_address.public_key,
                    amt=price_diff,
                ),
                AssetTransferTxn(
                    sender=escrow_address.public_key,
                    sp=suggested_params,
                    receiver=account_address.public_key,
                    index=nft_id,
                    amt=1,
                ),
                PaymentTxn(
                    escrow_address.public_key,
                    suggested_params,
                    seller_address.public_key,
                    price_with_fee,
                ),
                PaymentTxn(
                    escrow_address.public_key,
                    suggested_params,
                    fee_1_address.public_key,
                    fee // 2,
                ),
                PaymentTxn(
                    escrow_address.public_key,
                    suggested_params,
                    fee_2_address.public_key,
                    fee // 2,
                ),
            ]
            signers = [
                account_address,
                account_address,
                account_address,
                escrow_address,
                escrow_address,
                escrow_address,
                escrow_address,
            ]
        else:
            tx_group = [
                ApplicationCallTxn(
                    sender=account_address.public_key,
                    sp=suggested_params,
                    index=app_id,
                    on_complete=OnComplete.NoOpOC,
                    app_args=[ALGOWORLD_APP_ARGS.BUY_NOW],
                ),
                PaymentTxn(
                    account_address.public_key,
                    suggested_params,
                    escrow_address.public_key,
                    suggested_params.min_fee * 5,
                ),
                PaymentTxn(
                    escrow_address.public_key,
                    suggested_params,
                    account_address.public_key,
                    abs(price_diff),
                ),
                AssetTransferTxn(
                    sender=escrow_address.public_key,
                    sp=suggested_params,
                    receiver=account_address.public_key,
                    index=nft_id,
                    amt=1,
                ),
                PaymentTxn(
                    escrow_address.public_key,
                    suggested_params,
                    seller_address.public_key,
                    price_with_fee,
                ),
                PaymentTxn(
                    escrow_address.public_key,
                    suggested_params,
                    fee_1_address.public_key,
                    fee // 2,
                ),
                PaymentTxn(
                    escrow_address.public_key,
                    suggested_params,
                    fee_2_address.public_key,
                    fee // 2,
                ),
            ]
            signers = [
                account_address,
                account_address,
                escrow_address,
                escrow_address,
                escrow_address,
                escrow_address,
                escrow_address,
            ]

        tx = group_sign_send_wait(signers, tx_group)
        return tx
