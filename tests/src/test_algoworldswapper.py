"""Module for Algorand smart contracts integration testing."""

import base64

import pytest
from algosdk import constants
from algosdk.encoding import encode_address, is_valid_address
from algosdk.error import AlgodHTTPError, TemplateInputError

from src.contracts import (
    BANK_ACCOUNT_FEE,
    create_bank_transaction,
    create_split_transaction,
    setup_bank_contract,
    setup_split_contract,
)
from src.utils import (
    account_balance,
    call_sandbox_command,
    send_payment_transaction,
    add_standalone_account,
    create_payment_transaction,
    fund_account,
    process_logic_sig_transaction,
    process_transactions,
    logic_signature,
    suggested_params,
    transaction_info,
)
from src.algoworldswapper import SwapperContractHelper


def setup_module(module):
    """Ensure Algorand Sandbox is up prior to running tests from this module."""
    # call_sandbox_command("clean")
    call_sandbox_command("up")
    # call_sandbox_command("up", "dev")

class TestAlgoWorldSwapper:
    def setup_method(self):
        """Create receiver account before each test."""
        _, self.bob = add_standalone_account()
        _, self.alice = add_standalone_account()

    def _create_swapper_contract(self, **kwargs):
        """Helper method for creating bank contract from pre-existing receiver

        and provided named arguments.
        """
        _, swapper_escrow = SwapperContractHelper.setup_swapper_contract(self.bob, 10, 20, 400)
        return swapper_escrow

    def test_deposit(self):
        """Contract creation function `setup_bank_contract` should create new receiver

        if existing is not provided to it.
        """
        swapper_escrow_address = self._create_swapper_contract()
        payment_transaction = send_payment_transaction(
            self.bob, swapper_escrow_address, 0.01, "escrow_funding"
        )

        assert True

