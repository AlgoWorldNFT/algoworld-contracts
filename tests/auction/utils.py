import base64
from random import randint

from algosdk.encoding import encode_address
from algosdk.future.transaction import (
    ApplicationCallTxn,
    ApplicationCreateTxn,
    AssetOptInTxn,
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
from tests.models import LogicSigWallet, Wallet

ALGOD = _algod_client()
INDEXER = _indexer_client()
CONTRACT_CREATION_FEE = 466_000
CONTRACT_CONFIG_FEE = 302_000


class ALGOWORLD_APP_ARGS:
    ESCROW_ADDRESS = b"E"
    ASK_PRICE = b"A"
    BIDS_AMOUNT = b"B"
    OWNER_ADDRESS = b"O"
    CREATOR_ADDRESS = b"C"
    BID_PRICE = b"B"
    BID = b"B"
    SET_PRICE = b"S"
    BUY_NOW = b"BN"
    SELL_NOW = b"SN"
    CONFIGURE = b"C"


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


def get_global_state(app_arg: bytes, app_id: int):
    global_state = ALGOD.application_info(app_id)["params"]["global-state"]
    decoded_global_state = decode_global_state(global_state)
    return decoded_global_state[app_arg.decode()]


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
            "I am a fee transaction for configuring algoworld contract",
        )

        config_tx = ApplicationCallTxn(
            sender=creator_address.public_key,
            sp=ALGOD.suggested_params(),
            index=app_id,
            on_complete=OnComplete.NoOpOC,
            app_args=[ALGOWORLD_APP_ARGS.CONFIGURE],
            accounts=[escrow.public_key],
            note="I am a fee transaction for configuring algoworld contract",
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
