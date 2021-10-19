from dataclasses import dataclass


@dataclass
class Wallet():
    private_key: str
    public_key: str


@dataclass
class LogicSigWallet():
    logicsig: str
    public_key: str
