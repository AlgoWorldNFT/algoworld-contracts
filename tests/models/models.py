from dataclasses import dataclass


## Common Models
@dataclass
class Wallet:
    private_key: str
    public_key: str


@dataclass
class LogicSigWallet:
    logicsig: str
    public_key: str


@dataclass
class AlgorandSandbox:
    algod_container_name: str
    indexer_container_name: str
    algod_api_url: str
    indexer_api_url: str


## Auction models


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


@dataclass
class GlobalStateConditional:
    arg_name: ALGOWORLD_APP_ARGS
    arg_value: str
    expected_value: str


@dataclass
class LocalStateConditional:
    arg_name: ALGOWORLD_APP_ARGS
    account: Wallet
    arg_value: str
    expected_value: str
