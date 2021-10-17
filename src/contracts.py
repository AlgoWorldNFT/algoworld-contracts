"""Module containing domain logic for smart contracts creation."""

import json

from algosdk import template
from pyteal import Addr, And, Global, Int, Mode, Txn, TxnType, compileTeal

from src.utils import (
    account_balance,
    add_standalone_account,
    create_payment_transaction,
    fund_account,
    process_logic_sig_transaction,
    process_transactions,
    logic_signature,
    suggested_params,
    transaction_info,
)

BANK_ACCOUNT_FEE = 1000


# # BANK CONTRACT
def bank_for_account(receiver):
    """Only allow receiver to withdraw funds from this contract account.

    Args:
        receiver (str): Base 32 Algorand address of the receiver.
    """

    is_payment = Txn.type_enum() == TxnType.Payment
    is_single_tx = Global.group_size() == Int(1)
    is_correct_receiver = Txn.receiver() == Addr(receiver)
    no_close_out_addr = Txn.close_remainder_to() == Global.zero_address()
    no_rekey_addr = Txn.rekey_to() == Global.zero_address()
    acceptable_fee = Txn.fee() <= Int(BANK_ACCOUNT_FEE)

    return And(
        is_payment,
        is_single_tx,
        is_correct_receiver,
        no_close_out_addr,
        no_rekey_addr,
        acceptable_fee,
    )


def create_bank_transaction(logic_sig, escrow_address, receiver, amount, fee=1000):
    """Create bank transaction with provided amount."""
    params = suggested_params()
    params.fee = fee
    params.flat_fee = True
    payment_transaction = create_payment_transaction(
        escrow_address, params, receiver, amount
    )
    transaction_id = process_logic_sig_transaction(logic_sig, payment_transaction)
    return transaction_id


def setup_bank_contract(**kwargs):
    """Initialize and return bank contract for provided receiver."""
    receiver = kwargs.pop("receiver", add_standalone_account()[1])

    teal_source = compileTeal(
        bank_for_account(receiver),
        mode=Mode.Signature,
        version=3,
    )
    logic_sig = logic_signature(teal_source)
    escrow_address = logic_sig.address()
    fund_account(escrow_address)
    return logic_sig, escrow_address, receiver


# # SPLIT CONTRACT
def _create_grouped_transactions(split_contract, amount):
    """Create grouped transactions for the provided `split_contract` and `amount`."""
    params = suggested_params()
    return split_contract.get_split_funds_transaction(
        split_contract.get_program(),
        amount,
        1,
        params.first,
        params.last,
        params.gh,
    )


def _create_split_contract(
    owner,
    receiver_1,
    receiver_2,
    rat_1=1,
    rat_2=3,
    expiry_round=5000000,
    min_pay=3000,
    max_fee=2000,
):
    """Create and return split template instance from the provided arguments."""
    return template.Split(
        owner, receiver_1, receiver_2, rat_1, rat_2, expiry_round, min_pay, max_fee
    )


def create_split_transaction(split_contract, amount):
    """Create transaction with provided amount for provided split contract."""
    transactions = _create_grouped_transactions(split_contract, amount)
    transaction_id = process_transactions(transactions)
    return transaction_id


def setup_split_contract(**kwargs):
    """Initialize and return split contract instance based on provided named arguments."""
    owner = kwargs.pop("owner", add_standalone_account()[1])
    receiver_1 = kwargs.pop("receiver_1", add_standalone_account()[1])
    receiver_2 = kwargs.pop("receiver_2", add_standalone_account()[1])

    split_contract = _create_split_contract(owner, receiver_1, receiver_2, **kwargs)
    escrow_address = split_contract.get_address()
    fund_account(escrow_address)
    return split_contract


if __name__ == "__main__":
    """Example usage for contracts."""

    _, local_receiver = add_standalone_account()
    amount = 5000000
    logic_sig, escrow_address, receiver = setup_bank_contract(receiver=local_receiver)
    assert receiver == local_receiver

    transaction_id = create_bank_transaction(
        logic_sig, escrow_address, local_receiver, amount
    )
    print("amount: %s" % (amount,))
    print("escrow: %s" % (escrow_address))
    print("balance_escrow: %s" % (account_balance(escrow_address),))
    print("balance_receiver: %s" % (account_balance(local_receiver),))
    print(json.dumps(transaction_info(transaction_id), indent=2))

    print("\n\n")

    _, local_owner = add_standalone_account()
    _, local_receiver_2 = add_standalone_account()
    amount = 5000000

    split_contract = setup_split_contract(
        owner=local_owner,
        receiver_2=local_receiver_2,
        rat_1=3,
        rat_2=7,
    )
    assert split_contract.owner == local_owner
    assert split_contract.receiver_2 == local_receiver_2

    transaction_id = create_split_transaction(split_contract, amount)

    print("amount: %s" % (amount,))

    print("escrow: %s" % (split_contract.get_address(),))
    print("balance_escrow: %s" % (account_balance(split_contract.get_address()),))
    print("owner: %s" % (split_contract.owner,))
    print("balance_owner: %s" % (account_balance(split_contract.owner),))
    print("receiver_1: %s" % (split_contract.receiver_1,))
    print("balance_1: %s" % (account_balance(split_contract.receiver_2),))
    print(
        "receiver_2: %s" % (split_contract.receiver_2),
    )
    print("balance_2: %s" % (account_balance(split_contract.receiver_2),))
    print(json.dumps(transaction_info(transaction_id), indent=2))
