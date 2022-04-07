from dataclasses import dataclass


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
