"""Module for Algorand smart contracts integration testing."""


import pytest
from algosdk.future.transaction import AssetTransferTxn, LogicSigTransaction, PaymentTxn

from src.algoworldswapper import SwapConfig, compile_stateless, swapper
from tests import utils as Utils
from tests.models import LogicSigWallet, Wallet

Utils.call_sandbox_command("up")

BOB: Wallet = Utils.generate_wallet()
ALICE: Wallet = Utils.generate_wallet()

Utils.fund_wallet(BOB)
Utils.fund_wallet(ALICE)

BOB_ASSET_ID = Utils.mint_asa(BOB.public_key, BOB.private_key, "ASA_B", 1, 0)
ALICE_ASSET_ID = Utils.mint_asa(ALICE.public_key, ALICE.private_key, "ASA_B", 1, 0)

Utils.opt_in_asa(BOB, ALICE_ASSET_ID)
Utils.opt_in_asa(ALICE, BOB_ASSET_ID)

INITIAL_SWAPPER_CONFIG = compile_stateless(
    swapper(SwapConfig(BOB.public_key, BOB_ASSET_ID, ALICE_ASSET_ID, 1000000))
)
SWAPPER: LogicSigWallet = Utils.generate_stateless_contract(INITIAL_SWAPPER_CONFIG)


# compiled_swapper = compile_stateless(swapper(SwapConfig(BOB.public_key, BOB_ASSET_ID, ALICE_ASSET_ID, 1000000))) #Utils.suggested_params().last + 1000)))
# SWAPPER = Utils.generate_stateless_contract(compiled_swapper)


class TestAlgoWorldSwapper:
    def test_card_optin(self):
        """Test initial swapper setup from originator wallet (Bob)

        Initiates an atomic transaction with:
        1. Fee from Bob to cover swapper to opt-in to desired Asset A (the card that Bob is offering)
        2. Swapper performing opt-in to Asset A
        """

        bob_to_swapper_tx = PaymentTxn(
            BOB.public_key,
            Utils.suggested_params(),
            SWAPPER.public_key,
            int((0.2 + 0.01) * 1e6),
            None,
            "Covering escrow opt-in fee".encode(),
        )

        swapper_optin_tx = AssetTransferTxn(
            sender=SWAPPER.public_key,
            sp=Utils.suggested_params(),
            receiver=SWAPPER.public_key,
            amt=0,
            index=BOB_ASSET_ID,
        )

        Utils.calculate_and_assign_group_ids([bob_to_swapper_tx, swapper_optin_tx])

        signed_bob_to_swapper_tx = bob_to_swapper_tx.sign(BOB.private_key)
        signed_swapper_optin_tx = LogicSigTransaction(
            swapper_optin_tx, SWAPPER.logicsig
        )

        Utils.process_transactions([signed_bob_to_swapper_tx, signed_swapper_optin_tx])

        assert True

    @pytest.mark.depends(on=["test_card_optin"])
    def test_card_deposit(self):
        """Test initial card deposit
        """

        bob_to_swapper_tx = AssetTransferTxn(
            sender=BOB.public_key,
            sp=Utils.suggested_params(),
            receiver=SWAPPER.public_key,
            amt=1,
            index=BOB_ASSET_ID,
        )

        signed_bob_to_swapper_tx = bob_to_swapper_tx.sign(BOB.private_key)

        Utils.process_transactions([signed_bob_to_swapper_tx])

        assert True

    @pytest.mark.depends(on=["test_card_deposit"])
    def test_cards_swap(self):
        """Test main swapper logic
        """

        escrow_to_alice_txn = AssetTransferTxn(
            sender=SWAPPER.public_key,
            sp=Utils.suggested_params(),
            receiver=ALICE.public_key,
            amt=1,
            index=BOB_ASSET_ID,
        )

        alice_to_bob_txn = AssetTransferTxn(
            sender=ALICE.public_key,
            sp=Utils.suggested_params(),
            receiver=BOB.public_key,
            amt=1,
            index=ALICE_ASSET_ID,
        )

        Utils.calculate_and_assign_group_ids([escrow_to_alice_txn, alice_to_bob_txn])

        signed_escrow_to_alice_txn = LogicSigTransaction(
            escrow_to_alice_txn, SWAPPER.logicsig
        )
        signed_alice_to_bob_txn = alice_to_bob_txn.sign(ALICE.private_key)

        Utils.process_transactions(
            [signed_escrow_to_alice_txn, signed_alice_to_bob_txn]
        )

        assert True

    # TODO : Needs refining and parametrizing
    # @pytest.mark.depends(on=['test_cards_swap'])
    # def test_close_swap(self):
    #     """Test main swapper logic
    #     """

    #     escrow_asa_to_bob_tx = AssetTransferTxn(
    #         sender=SWAPPER.public_key,
    #         sp=Utils.suggested_params(),
    #         close_assets_to=BOB.public_key,
    #         receiver=BOB.public_key,
    #         amt=1,
    #         index=BOB_ASSET_ID)

    #     escrow_closeout_tx = PaymentTxn(SWAPPER.public_key, Utils.suggested_params(), BOB.public_key, int(0), close_remainder_to=BOB.public_key, note="Covering escrow opt-in fee".encode())

    #     bob_proof_tx = PaymentTxn(BOB.public_key, Utils.suggested_params(), BOB.public_key, int(0), None, "Covering escrow opt-in fee".encode())

    #     Utils.calculate_and_assign_group_ids([escrow_asa_to_bob_tx, escrow_closeout_tx, bob_proof_tx])

    #     signed_escrow_asa_to_bob_tx = LogicSigTransaction(escrow_asa_to_bob_tx, SWAPPER.logicsig)
    #     signed_escrow_closeout_tx = LogicSigTransaction(escrow_closeout_tx, SWAPPER.logicsig)
    #     signed_bob_proof_tx = bob_proof_tx.sign(BOB.private_key)

    #     Utils.process_transactions([signed_escrow_asa_to_bob_tx, signed_escrow_closeout_tx, signed_bob_proof_tx])

    #     assert True
