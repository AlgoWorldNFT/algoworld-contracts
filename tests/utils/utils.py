"""Module containing helper functions for accessing Algorand blockchain."""

import base64
import os
import pty
import subprocess
import time
from pathlib import Path
from typing import List

import yaml
from algosdk import account, mnemonic
from algosdk.error import IndexerHTTPError
from algosdk.future.transaction import (
    AssetConfigTxn,
    AssetTransferTxn,
    LogicSig,
    PaymentTxn,
    Transaction,
    calculate_group_id,
)
from algosdk.v2client import algod, indexer

from tests.models import LogicSigWallet, Wallet

INDEXER_TIMEOUT = 10  # 61 for devMode


## SANDBOX
################################################################
def _cli_passphrase_for_account(address):
    """Return passphrase for provided address."""
    process = call_sandbox_command("goal", "account", "export", "-a", address)

    if process.stderr:
        raise RuntimeError(process.stderr.decode("utf8"))

    passphrase = ""
    parts = process.stdout.decode("utf8").split('"')
    if len(parts) > 1:
        passphrase = parts[1]
    if passphrase == "":
        raise ValueError(
            "Can't retrieve passphrase from the address: %s\nOutput: %s"
            % (address, process.stdout.decode("utf8"))
        )
    return passphrase


def _sandbox_directory():
    """Return full path to Algorand's sandbox executable.

    The location of sandbox directory is retrieved either from the ALGORAND_SANBOX_DIR
    environment variable or if it's not set then the location of sandbox directory
    is implied to be the sibling of this Django project in the directory tree.
    """
    return os.environ.get("ALGORAND_SANBOX_DIR") or str(
        Path(__file__).resolve().parent.parent.parent.parent / "sandbox"
    )


def _sandbox_executable():
    """Return full path to Algorand's sandbox executable."""
    return _sandbox_directory() + "/sandbox"


def call_sandbox_command(*args):
    """Call and return sandbox command composed from provided arguments."""
    return subprocess.run(
        [_sandbox_executable(), *args], stdin=pty.openpty()[1], capture_output=True
    )


## CLIENTS
################################################################
def _algod_client():
    """Instantiate and return Algod client object."""
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    return algod.AlgodClient(algod_token, algod_address)


def _indexer_client():
    """Instantiate and return Indexer client object."""
    indexer_address = "http://localhost:8980"
    indexer_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    return indexer.IndexerClient(indexer_token, indexer_address)


## TRANSACTIONS
################################################################
def _add_transaction(sender, receiver, passphrase, amount, note):
    """Create and sign transaction from provided arguments.

    Returned non-empty tuple carries field where error was raised and description.
    If the first item is None then the error is non-field/integration error.
    Returned two-tuple of empty strings marks successful transaction.
    """
    client = _algod_client()
    params = client.suggested_params()
    unsigned_txn = PaymentTxn(sender, params, receiver, amount, None, note.encode())
    signed_txn = unsigned_txn.sign(mnemonic.to_private_key(passphrase))
    transaction_id = client.send_transaction(signed_txn)
    wait_for_confirmation(client, transaction_id, 4)
    return transaction_id


def wait_for_confirmation(client, transaction_id, timeout):
    """
    Wait until the transaction is confirmed or rejected, or until 'timeout'
    number of rounds have passed.
    Args:
        transaction_id (str): the transaction to wait for
        timeout (int): maximum number of rounds to wait
    Returns:
        dict: pending transaction information, or throws an error if the transaction
            is not confirmed or rejected in the next timeout rounds
    """
    start_round = client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception("pool error: {}".format(pending_txn["pool-error"]))
        client.status_after_block(current_round)
        current_round += 1
    raise Exception(
        "pending tx not found in timeout rounds, timeout value = : {}".format(timeout)
    )


def process_transactions(transactions):
    """Send provided grouped `transactions` to network and wait for confirmation."""
    client = _algod_client()
    transaction_id = client.send_transactions(transactions)
    wait_for_confirmation(client, transaction_id, 4)
    return transaction_id


def suggested_params():
    """Return the suggested params from the algod client."""
    return _algod_client().suggested_params()


## CREATING
################################################################
def generate_wallet():
    """Create standalone account and return two-tuple of its private key and address."""
    private_key, public_key = account.generate_account()
    return Wallet(private_key, public_key)


def generate_stateless_contract(compiled_teal: str) -> LogicSigWallet:
    """Initialize and return bank contract for provided receiver."""

    logic_sig = logic_signature(compiled_teal)
    escrow_address = logic_sig.address()
    return LogicSigWallet(logic_sig, escrow_address)


def fund_wallet(wallet: Wallet, initial_funds: int = int(10 * 1e6)):
    """Fund provided `address` with `initial_funds` amount of microAlgos."""
    initial_funds_address = _initial_funds_address()
    if initial_funds_address is None:
        raise Exception("Initial funds weren't transferred!")
    _add_transaction(
        initial_funds_address,
        wallet.public_key,
        _cli_passphrase_for_account(initial_funds_address),
        initial_funds,
        "Initial funds",
    )


def calculate_and_assign_group_ids(transactions: List[Transaction]):
    gid = calculate_group_id(transactions)

    for transaction in transactions:
        transaction.group = gid


## RETRIEVING
################################################################
def _initial_funds_address():
    """Get the address of initially created account having enough funds.

    Such an account is used to transfer initial funds for the accounts
    created in this tutorial.
    """
    return next(
        (
            account.get("address")
            for account in _indexer_client().accounts().get("accounts", [{}, {}])
            if account.get("created-at-round") == 0
            and account.get("status") == "Offline"  # "Online" for devMode
        ),
        None,
    )


def account_balance(address):
    """Return funds balance of the account having provided address."""
    account_info = _algod_client().account_info(address)
    return account_info.get("amount")


def transaction_info(transaction_id):
    """Return transaction with provided id."""
    timeout = 0
    while timeout < INDEXER_TIMEOUT:
        try:
            transaction = _indexer_client().transaction(transaction_id)
            break
        except IndexerHTTPError:
            time.sleep(1)
            timeout += 1
    else:
        raise TimeoutError(
            "Timeout reached waiting for transaction to be available in indexer"
        )

    return transaction


## UTILITY
################################################################
def _compile_source(source):
    """Compile and return teal binary code."""
    compile_response = _algod_client().compile(source)
    return base64.b64decode(compile_response["result"])


def logic_signature(teal_source):
    """Create and return logic signature for provided `teal_source`."""
    compiled_binary = _compile_source(teal_source)
    return LogicSig(compiled_binary)


def parse_params(args, scParam):

    # decode external parameter and update current values.
    # (if an external paramter is passed)
    try:
        param = yaml.safe_load(args)
        for key, value in param.items():
            scParam[key] = value
        return scParam
    except yaml.YAMLError as exc:
        print(exc)


## ASA
################################################################
def mint_asa(sender: str, sender_pass: str, asset_name: str, total: int, decimals: int):
    """Return transaction with provided id."""
    algod_client = _algod_client()
    params = algod_client.suggested_params()

    txn = AssetConfigTxn(
        sender=sender,
        sp=params,
        total=total,
        default_frozen=False,
        unit_name=asset_name,
        asset_name=asset_name,
        manager=sender,
        reserve=sender,
        freeze=sender,
        clawback=sender,
        url="https://path/to/my/asset/details",
        decimals=decimals,
    )
    # Sign with secret key of creator
    stxn = txn.sign(sender_pass)

    # Send the transaction to the network and retrieve the txid.
    txid = algod_client.send_transaction(stxn)
    print(txid)

    # Retrieve the asset ID of the newly created asset by first
    # ensuring that the creation transaction was confirmed,
    # then grabbing the asset id from the transaction.

    # Wait for the transaction to be confirmed
    wait_for_confirmation(algod_client, txid, 4)

    ptx = algod_client.pending_transaction_info(txid)

    return ptx["asset-index"]


def opt_in_asa(wallet: Wallet, asset_id: int):
    """Return transaction with provided id."""
    algod_client = _algod_client()
    params = algod_client.suggested_params()

    txn = AssetTransferTxn(
        sender=wallet.public_key,
        sp=params,
        receiver=wallet.public_key,
        amt=0,
        index=asset_id,
    )

    # Sign with secret key of creator
    stxn = txn.sign(wallet.private_key)

    # Send the transaction to the network and retrieve the txid.
    txid = algod_client.send_transaction(stxn)

    return txid
