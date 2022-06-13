import os
import unittest

from hmt_escrow.eth_bridge import (
    get_hmtoken,
    get_factory,
    get_escrow,
    get_pub_key_from_addr,
    handle_transaction,
    set_pub_key_at_addr
)
from test.hmt_escrow.utils import create_job


class EthBridgeTestCase(unittest.TestCase):
    def setUp(self):
        self.credentials = {
            "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
            "gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        }
        self.rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        self.job = create_job()

    def test_handle_transaction(self):
        from web3.datastructures import AttributeDict as Web3AttributeDict

        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        gas = 4712388
        hmt_amount = int(self.job.amount * 10 ** 18)
        hmtoken_contract = get_hmtoken()
        txn_func = hmtoken_contract.functions.transfer
        func_args = [self.job.job_contract.address, hmt_amount]
        txn_info = {
            "gas_payer": self.job.gas_payer,
            "gas_payer_priv": self.job.gas_payer_priv,
            "gas": gas,
        }
        txn_receipt = handle_transaction(txn_func, *func_args, **txn_info)
        self.assertIs(type(txn_receipt), Web3AttributeDict)

    def test_get_escrow(self):
        self.job.launch(self.rep_oracle_pub_key)
        self.assertIsNotNone(get_escrow(self.job.job_contract.address))

    def test_get_factory(self):
        self.assertIsNotNone(get_factory(self.job.factory_contract.address))

    def test_get_pub_key_from_address(self):
        with self.assertRaises(ValueError):
            get_pub_key_from_addr("badaddress")
        os.environ["GAS_PAYER"] = self.credentials["gas_payer"]
        os.environ["GAS_PAYER_PRIV"] = self.credentials["gas_payer_priv"]
        set_pub_key_at_addr(self.rep_oracle_pub_key)
        self.assertEqual(
            get_pub_key_from_addr(os.environ["GAS_PAYER"]),
            self.rep_oracle_pub_key
        )

    def test_set_pub_key_at_address(self):
        os.environ["GAS_PAYER"] = self.credentials["gas_payer"]
        os.environ["GAS_PAYER_PRIV"] = self.credentials["gas_payer_priv"]
        self.assertIsNotNone(
            set_pub_key_at_addr(self.rep_oracle_pub_key).transactionHash
        )


if __name__ == "__main__":
    unittest.main(exit=True)
