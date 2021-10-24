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
    LogicSigTransaction,
    PaymentTxn,
    SignedTransaction,
    Transaction,
    calculate_group_id,
    wait_for_confirmation,
    write_to_file,
)
from algosdk.v2client import algod, indexer

from src.algoworldswapper import OPTIN_FUNDING_AMOUNT
from tests.models import LogicSigWallet, Wallet

INDEXER_TIMEOUT = 10  # 61 for devMode


# SANDBOX
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

    The location of sandbox directory is retrieved either from the
    ALGORAND_SANBOX_DIR environment variable or if it's not set then the
    location of sandbox directory is implied to be the sibling of this Django
    project in the directory tree.
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


# CLIENTS
################################################################
def _algod_client():
    """Instantiate and return Algod client object."""
    algod_address = "http://localhost:4001"
    algod_token = "a" * 64
    return algod.AlgodClient(algod_token, algod_address)


def _indexer_client():
    """Instantiate and return Indexer client object."""
    indexer_address = "http://localhost:8980"
    indexer_token = "a" * 64
    return indexer.IndexerClient(indexer_token, indexer_address)


# TRANSACTIONS
################################################################
def _add_transaction(sender, receiver, passphrase, amount, note):
    """Create and sign transaction from provided arguments.

    Returned non-empty tuple carries field where error was raised and
    description.
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


def process_transactions(transactions):
    """
    Send provided grouped `transactions` to network and wait for confirmation.
    """
    client = _algod_client()
    transaction_id = client.send_transactions(transactions)
    wait_for_confirmation(client, transaction_id, 4)
    return transaction_id


def suggested_params():
    """Return the suggested params from the algod client."""
    return _algod_client().suggested_params()


def sign(wallet, txn: Transaction) -> SignedTransaction:
    if isinstance(wallet, LogicSigWallet):
        return LogicSigTransaction(txn, wallet.logicsig)  # type: ignore

    assert wallet.private_key
    return txn.sign(wallet.private_key)


def sign_send_wait(wallet: Wallet, txn: Transaction):
    """Sign a transaction, submit it, and wait for its confirmation."""
    signed_txn = sign(wallet, txn)
    tx_id = signed_txn.transaction.get_txid()

    # Facilitating TEAL debugging
    write_to_file([signed_txn], "/tmp/txn.signed", overwrite=True)

    algod_client = _algod_client()
    algod_client.send_transactions([signed_txn])
    wait_for_confirmation(algod_client, tx_id, 4)
    return algod_client.pending_transaction_info(tx_id)


def group_sign_send_wait(signers: List, txns: List[Transaction]):
    """
    Sign and send group transaction to network and wait for confirmation.
    """

    assert len(signers) == len(txns)
    signed_group = []
    gid = calculate_group_id(txns)

    for signer, t in zip(signers, txns):
        t.group = gid
        signed_group.append(sign(signer, t))

    # Facilitating TEAL debugging
    write_to_file(signed_group, "/tmp/txn.signed", overwrite=True)

    algod_client = _algod_client()
    gtxn_id = algod_client.send_transactions(signed_group)
    wait_for_confirmation(algod_client, gtxn_id, 4)
    return algod_client.pending_transaction_info(gtxn_id)


# CREATING
################################################################
def generate_wallet():
    """
    Create standalone account and return two-tuple of its private key and
    address.
    """
    private_key, public_key = account.generate_account()
    return Wallet(private_key, public_key)


def generate_stateless_contract(compiled_teal: str) -> LogicSigWallet:
    """Initialize and return bank contract for provided receiver."""

    logic_sig = logic_signature(compiled_teal)
    escrow_address = logic_sig.address()
    return LogicSigWallet(logic_sig, escrow_address)  # type: ignore


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


# RETRIEVING
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
            and account.get("status") == "Online"  # "Online" for devMode
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


# UTILITY
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


# ASA
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
        unit_name="",
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

    # Retrieve the asset ID of the newly created asset by first
    # ensuring that the creation transaction was confirmed,
    # then grabbing the asset id from the transaction.

    # Wait for the transaction to be confirmed
    wait_for_confirmation(algod_client, txid, 4)

    ptx = algod_client.pending_transaction_info(txid)

    asset_id = ptx["asset-index"]

    print(f"\n --- ASA {asset_name} - {asset_id} minted.")

    return asset_id


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

    print(f"\n --- Account {wallet.public_key} opted-in ASA {asset_id}.")

    return txid


def swapper_opt_in(
    swap_creator: Wallet,
    swapper_account: LogicSigWallet,
    asset_id: int,
    asset_amount: int = 0,
    funding_amount: int = OPTIN_FUNDING_AMOUNT,
):
    algod_client = _algod_client()
    params = algod_client.suggested_params()

    optin_fee_txn = PaymentTxn(
        sender=swap_creator.public_key,
        sp=params,
        receiver=swapper_account.public_key,
        amt=funding_amount,
    )

    asa_optin_txn = AssetTransferTxn(
        sender=swapper_account.public_key,
        sp=params,
        receiver=swapper_account.public_key,
        amt=asset_amount,
        index=asset_id,
    )

    group_sign_send_wait(
        [swap_creator, swapper_account], [optin_fee_txn, asa_optin_txn]
    )

    print(f"\n --- Swapper {swapper_account.public_key} opted-in ASA {asset_id}.")


def swapper_deposit(
    swap_creator: Wallet,
    swapper_account: LogicSigWallet,
    asset_id: int,
    asset_amount: int = 1,
):
    algod_client = _algod_client()
    params = algod_client.suggested_params()

    deposit_asa_txn = AssetTransferTxn(
        sender=swap_creator.public_key,
        sp=params,
        receiver=swapper_account.public_key,
        amt=asset_amount,
        index=asset_id,
    )

    sign_send_wait(swap_creator, deposit_asa_txn)

    print(
        f"\n --- Account {swap_creator.public_key} deposited {asset_amount} "
        f"units of ASA {asset_id} into {swapper_account.public_key}."
    )


def asa_swap(
    offered_asset_sender: LogicSigWallet,
    offered_asset_receiver: Wallet,
    offered_asset_id: int,
    offered_asset_amt: int,
    requested_asset_sender: Wallet,
    requested_asset_receiver: Wallet,
    requested_asset_id: int,
    requested_asset_amt: int,
):
    algod_client = _algod_client()
    params = algod_client.suggested_params()

    offered_asa_xfer_txn = AssetTransferTxn(
        sender=offered_asset_sender.public_key,
        sp=params,
        receiver=offered_asset_receiver.public_key,
        amt=offered_asset_amt,
        index=offered_asset_id,
    )

    requested_asa_xfer_txn = AssetTransferTxn(
        sender=requested_asset_sender.public_key,
        sp=params,
        receiver=requested_asset_receiver.public_key,
        amt=requested_asset_amt,
        index=requested_asset_id,
    )

    group_sign_send_wait(
        [offered_asset_sender, requested_asset_sender],
        [offered_asa_xfer_txn, requested_asa_xfer_txn],
    )

    print(
        f"\n --- Account {offered_asset_sender.public_key} sent {offered_asset_amt} "
        f"units of ASA {offered_asset_id} to {offered_asset_receiver.public_key}."
    )
    print(
        f"\n --- Account {requested_asset_sender.public_key} sent {requested_asset_amt} "
        f"units of ASA {requested_asset_id} to {requested_asset_receiver.public_key}."
    )


def close_swap(
    asset_sender: LogicSigWallet,
    asset_receiver: Wallet,
    asset_close_to: Wallet,
    asset_id: int,
    swapper_funds_sender: LogicSigWallet,
    swapper_funds_receiver: Wallet,
    swapper_funds_close_to: Wallet,
    proof_sender: Wallet,
    proof_receiver: Wallet,
    asset_amt: int = 0,
    swapper_funds_amt: int = 0,
    proof_amt: int = 0,
):
    algod_client = _algod_client()
    params = algod_client.suggested_params()

    close_asa_txn = AssetTransferTxn(
        sender=asset_sender.public_key,
        sp=params,
        receiver=asset_receiver.public_key,
        amt=asset_amt,
        index=asset_id,
        close_assets_to=asset_close_to.public_key,
    )

    close_swap_txn = PaymentTxn(
        sender=swapper_funds_sender.public_key,
        sp=params,
        receiver=swapper_funds_receiver.public_key,
        amt=swapper_funds_amt,
        close_remainder_to=swapper_funds_close_to.public_key,
    )

    proof_txn = PaymentTxn(
        sender=proof_sender.public_key,
        sp=params,
        receiver=proof_receiver.public_key,
        amt=proof_amt,
    )

    group_sign_send_wait(
        [asset_sender, swapper_funds_sender, proof_sender],
        [close_asa_txn, close_swap_txn, proof_txn],
    )

    print(f"\n --- Account {proof_sender.public_key} closed Swapper.")
