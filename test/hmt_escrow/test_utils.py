import unittest
from unittest.mock import MagicMock, patch
import hmt_escrow.utils as utils
from hmt_escrow.eth_bridge import (
    get_hmtoken,
    handle_transaction,
)

from test.hmt_escrow.utils import create_job


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.credentials = {
            "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
            "gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        }
        self.rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        self.job = create_job()

    def test_parse_transfer_transaction_with_event_and_balance(self):
        """Test we return positive results for transaction with event and balance"""
        self.job.launch(self.rep_oracle_pub_key)
        gas = 4712388
        hmt_amount = int(self.job.amount * 10**18)
        hmtoken_contract = get_hmtoken()
        txn_func = hmtoken_contract.functions.transfer
        func_args = [self.job.job_contract.address, hmt_amount]
        txn_info = {
            "gas_payer": self.job.gas_payer,
            "gas_payer_priv": self.job.gas_payer_priv,
            "gas": gas,
        }
        txn_receipt = handle_transaction(txn_func, *func_args, **txn_info)

        hmt_transferred, tx_balance = utils.parse_transfer_transaction(
            hmtoken_contract, txn_receipt
        )

        self.assertTrue(hmt_transferred)
        self.assertEqual(tx_balance, hmt_amount)

    def test_parse_transfer_transaction_without_event(self):
        """Test we return negative results for transaction with empty event"""
        hmtoken_contract = MagicMock()
        tx_receipt = MagicMock()

        hmtoken_contract.events = hmtoken_contract
        hmtoken_contract.Transfer.return_value = hmtoken_contract
        hmtoken_contract.processReceipt.side_effect = [()]

        hmt_transferred, tx_balance = utils.parse_transfer_transaction(
            hmtoken_contract, tx_receipt
        )

        self.assertFalse(hmt_transferred)
        self.assertIsNone(tx_balance)

    def test_parse_transfer_broken_transaction(self):
        """Test we return negative results for transaction not empty without balance"""
        hmtoken_contract = MagicMock()
        tx_receipt = MagicMock()

        hmtoken_contract.events = hmtoken_contract
        hmtoken_contract.Transfer.return_value = hmtoken_contract
        hmtoken_contract.processReceipt.side_effect = [({"args": {}},)]

        hmt_transferred, tx_balance = utils.parse_transfer_transaction(
            hmtoken_contract, tx_receipt
        )

        self.assertFalse(hmt_transferred)
        self.assertIsNone(tx_balance)
