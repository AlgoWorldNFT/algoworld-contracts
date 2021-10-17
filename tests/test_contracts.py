# """Module for Algorand smart contracts integration testing."""

# import base64

# import pytest
# from algosdk import constants
# from algosdk.encoding import encode_address, is_valid_address
# from algosdk.error import AlgodHTTPError, TemplateInputError

# from src.contracts import (
#     BANK_ACCOUNT_FEE,
#     create_bank_transaction,
#     create_split_transaction,
#     setup_bank_contract,
#     setup_split_contract,
# )
# from src.utils import (
#     account_balance,
#     add_standalone_account,
#     call_sandbox_command,
#     transaction_info,
# )


# def setup_module(module):
#     """Ensure Algorand Sandbox is up prior to running tests from this module."""
#     call_sandbox_command("up")
#     # call_sandbox_command("up", "dev")


# class TestBankContract:
#     """Class for testing the bank for account smart contract."""

#     def setup_method(self):
#         """Create receiver account before each test."""
#         _, self.receiver = add_standalone_account()

#     def _create_bank_contract(self, **kwargs):
#         """Helper method for creating bank contract from pre-existing receiver

#         and provided named arguments.
#         """
#         return setup_bank_contract(receiver=self.receiver, **kwargs)

#     def test_bank_contract_creates_new_receiver(self):
#         """Contract creation function `setup_bank_contract` should create new receiver

#         if existing is not provided to it.
#         """
#         _, _, receiver = setup_bank_contract()
#         assert receiver != self.receiver

#     def test_bank_contract_uses_existing_receiver_when_it_is_provided(self):
#         """Provided receiver should be used in the smart contract."""
#         _, _, receiver = self._create_bank_contract()
#         assert receiver == self.receiver

#     def test_bank_contract_fee(self):
#         """Transaction should be created and error shouldn't be raised

#         when the fee is equal to BANK_ACCOUNT_FEE.
#         """
#         logic_sig, escrow_address, receiver = self._create_bank_contract()
#         transaction_id = create_bank_transaction(
#             logic_sig, escrow_address, receiver, 2000000, fee=BANK_ACCOUNT_FEE
#         )
#         assert len(transaction_id) > 48

#     def test_bank_contract_fee_failed_transaction(self):
#         """Transaction should fail when the fee is greater than BANK_ACCOUNT_FEE."""
#         fee = BANK_ACCOUNT_FEE + 1000
#         logic_sig, escrow_address, receiver = self._create_bank_contract()
#         with pytest.raises(AlgodHTTPError) as exception:
#             create_bank_transaction(
#                 logic_sig, escrow_address, receiver, 2000000, fee=fee
#             )
#         assert "rejected by logic" in str(exception.value)

#     def test_bank_contract_raises_error_for_wrong_receiver(self):
#         """Transaction should fail for a wrong receiver."""
#         _, other_receiver = add_standalone_account()

#         logic_sig, escrow_address, _ = self._create_bank_contract()
#         with pytest.raises(AlgodHTTPError) as exception:
#             create_bank_transaction(logic_sig, escrow_address, other_receiver, 2000000)
#         assert "rejected by logic" in str(exception.value)

#     @pytest.mark.parametrize(
#         "amount",
#         [1000000, 500000, 504213, 2500000],
#     )
#     def test_bank_contract_balances_of_involved_accounts(self, amount):
#         """After successful transaction, balance of involved accounts should pass

#         assertions to result of expressions calculated for the provided amount.
#         """
#         logic_sig, escrow_address, receiver = self._create_bank_contract(
#             fee=BANK_ACCOUNT_FEE
#         )
#         escrow_balance = account_balance(escrow_address)
#         create_bank_transaction(logic_sig, escrow_address, receiver, amount)

#         assert account_balance(receiver) == amount
#         assert (
#             account_balance(escrow_address)
#             == escrow_balance - amount - BANK_ACCOUNT_FEE
#         )

#     def test_bank_contract_transaction(self):
#         """Successful transaction should have sender equal to escrow account.

#         Also, the transaction type should be payment, payment receiver should be
#         contract's receiver, and the payment amount should be equal to provided amount.
#         Finally, there should be no group field in transaction.
#         """
#         amount = 1000000
#         logic_sig, escrow_address, receiver = self._create_bank_contract(
#             fee=BANK_ACCOUNT_FEE
#         )
#         transaction_id = create_bank_transaction(
#             logic_sig, escrow_address, receiver, amount
#         )
#         transaction = transaction_info(transaction_id)
#         assert transaction.get("transaction").get("tx-type") == constants.payment_txn
#         assert transaction.get("transaction").get("sender") == escrow_address
#         assert (
#             transaction.get("transaction").get("payment-transaction").get("receiver")
#             == receiver
#         )
#         assert (
#             transaction.get("transaction").get("payment-transaction").get("amount")
#             == amount
#         )
#         assert transaction.get("transaction").get("group", None) is None


# class TestSplitContract:
#     """Class for testing the split smart contract."""

#     def setup_method(self):
#         """Create owner and receivers accounts before each test."""
#         _, self.owner = add_standalone_account()
#         _, self.receiver_1 = add_standalone_account()
#         _, self.receiver_2 = add_standalone_account()

#     def _create_split_contract(self, **kwargs):
#         """Helper method for creating a split contract from pre-existing accounts

#         and provided named arguments.
#         """
#         return setup_split_contract(
#             owner=self.owner,
#             receiver_1=self.receiver_1,
#             receiver_2=self.receiver_2,
#             **kwargs,
#         )

#     def test_split_contract_creates_new_accounts(self):
#         """Contract creation function `setup_split_contract` should create new accounts

#         if existing are not provided to it.
#         """
#         contract = setup_split_contract()
#         assert contract.owner != self.owner
#         assert contract.receiver_1 != self.receiver_1
#         assert contract.receiver_2 != self.receiver_2

#     def test_split_contract_uses_existing_accounts_when_they_are_provided(self):
#         """Provided accounts should be used in the smart contract."""
#         contract = self._create_split_contract()
#         assert contract.owner == self.owner
#         assert contract.receiver_1 == self.receiver_1
#         assert contract.receiver_2 == self.receiver_2

#     def test_split_contract_min_pay(self):
#         """Transaction should be created when the split amount for receiver_1

#         is greater than `min_pay`.
#         """
#         min_pay = 250000
#         contract = self._create_split_contract(min_pay=min_pay, rat_1=1, rat_2=3)
#         amount = 2000000
#         create_split_transaction(contract, amount)
#         assert account_balance(contract.receiver_1) > min_pay

#     def test_split_contract_min_pay_failed_transaction(self):
#         """Transaction should fail when the split amount for receiver_1

#         is less than `min_pay`.
#         """
#         min_pay = 300000
#         contract = self._create_split_contract(min_pay=min_pay, rat_1=1, rat_2=3)
#         amount = 1000000

#         with pytest.raises(TemplateInputError) as exception:
#             create_split_transaction(contract, amount)
#         assert (
#             str(exception.value)
#             == f"the amount paid to receiver_1 must be greater than {min_pay}"
#         )

#     def test_split_contract_max_fee_failed_transaction(self):
#         """Transaction should fail for the fee greater than `max_fee`."""
#         max_fee = 500
#         contract = self._create_split_contract(max_fee=max_fee, rat_1=1, rat_2=3)
#         amount = 1000000

#         with pytest.raises(TemplateInputError) as exception:
#             create_split_transaction(contract, amount)
#         assert (
#             str(exception.value)
#             == f"the transaction fee should not be greater than {max_fee}"
#         )

#     @pytest.mark.parametrize(
#         "amount,rat_1,rat_2",
#         [
#             (1000000, 1, 2),
#             (1000033, 1, 3),
#             (1000000, 2, 5),
#         ],
#     )
#     def test_split_contract_invalid_ratios_for_amount(self, amount, rat_1, rat_2):
#         """Transaction should fail for every combination of provided amount and ratios."""
#         contract = self._create_split_contract(rat_1=rat_1, rat_2=rat_2)
#         with pytest.raises(TemplateInputError) as exception:
#             create_split_transaction(contract, amount)
#         assert (
#             str(exception.value)
#             == f"the specified amount cannot be split into two parts with the ratio {rat_1}/{rat_2}"
#         )

#     @pytest.mark.parametrize(
#         "amount,rat_1,rat_2",
#         [
#             (1000000, 1, 3),
#             (999999, 1, 2),
#             (1400000, 2, 5),
#             (1000000, 1, 9),
#             (900000, 4, 5),
#             (1200000, 5, 1),
#         ],
#     )
#     def test_split_contract_balances_of_involved_accounts(self, amount, rat_1, rat_2):
#         """After successful transaction, balance of involved accounts should pass

#         assertion to result of expressions calculated from the provided arguments.
#         """
#         contract = self._create_split_contract(rat_1=rat_1, rat_2=rat_2)
#         assert account_balance(contract.owner) == 0
#         assert account_balance(contract.receiver_1) == 0
#         assert account_balance(contract.receiver_2) == 0

#         escrow = contract.get_address()
#         escrow_balance = account_balance(escrow)

#         create_split_transaction(contract, amount)
#         assert account_balance(contract.owner) == 0
#         assert account_balance(contract.receiver_1) == rat_1 * amount / (rat_1 + rat_2)
#         assert account_balance(contract.receiver_2) == rat_2 * amount / (rat_1 + rat_2)
#         assert account_balance(escrow) == escrow_balance - amount - contract.max_fee


#     def test_split_contract_transaction(self):
#         """Successful transaction should have sender equal to escrow account.

#         Also, receiver should be contract's receiver_1, the type should be payment,
#         and group should be a valid address.
#         """
#         contract = setup_split_contract()
#         transaction_id = create_split_transaction(contract, 1000000)
#         transaction = transaction_info(transaction_id)
#         assert transaction.get("transaction").get("tx-type") == constants.payment_txn
#         assert transaction.get("transaction").get("sender") == contract.get_address()
#         assert (
#             transaction.get("transaction").get("payment-transaction").get("receiver")
#             == contract.receiver_1
#         )
#         assert is_valid_address(
#             encode_address(
#                 base64.b64decode(transaction.get("transaction").get("group"))
#             )
#         )
