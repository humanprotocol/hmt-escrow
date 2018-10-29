#!/usr/bin/env python3

import logging
import os
import sys
import unittest

import schematics
from unittest.mock import patch
from web3 import Web3

os.environ['HET_ETH_SERVER'] = os.getenv('HET_ETH_SERVER',
                                         "http://localhost:8545")
import api
import basemodels
from api.storage import _decrypt, _encrypt, upload

REQ_JSON = 'file:///tmp/req.json'
ANS_JSON = 'file:///tmp/ans.json'
CALLBACK_URL = 'http://google.com/webback'

ADDR = Web3.toChecksumAddress(
    os.getenv("TESTADDR", '0x1413862c2b7054cdbfdc181b83962cb0fc11fd92'))
TO_ADDR = '0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809'

PUB1 = b'b1bd4192dd7134d869f992fafcf4ed60ef8c566f2649b773f5562bc6736ff8dd8c459b36201dd8ce417cc96275a11f209942eacb14aef5b91a8e6ea0703b4bf8'
PRIV1 = b'657b6497a355a3982928d5515d48a84870f057c4d16923eb1d104c0afada9aa8'
PUB2 = b'94e67e63b2bf9b960b5a284aef8f4cc2c41ce08b083b89d17c027eb6f11994140d99c0aeadbf32fbcdac4785c5550bf28eefd0d339c74a033d55b1765b6503bf'
PRIV2 = b'f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1'

FAKE_ORACLE = ADDR
FAKE_URL = 'http://google.com/fake'
IMAGE_LABEL_BINARY = 'image_label_binary'

REP_ORACLE = Web3.toChecksumAddress(
    os.getenv("REP_ORACLE", "0x61F9F0B31eacB420553da8BCC59DC617279731Ac"))
REC_ORACLE = Web3.toChecksumAddress(
    os.getenv("REC_ORACLE", "0xD979105297fB0eee83F7433fC09279cb5B94fFC6"))


def a_manifest(number_of_tasks=100,
               bid_amount=1,
               expiration_date=0,
               minimum_trust=.1,
               request_type=IMAGE_LABEL_BINARY,
               job_mode='batch') -> basemodels.Manifest:
    manifest = basemodels.Manifest({
        'requester_restricted_answer_set': {
            '0': {
                'en': 'English Answer 1'
            },
            '1': {
                'en': 'English Answer 2',
                'answer_example_uri': 'https://hcaptcha.com/example_answer2.jpg'
            }
        },
        'job_mode':
        job_mode,
        'request_type':
        request_type,
        'unsafe_content':
        False,
        'task_bid_price':
        bid_amount,
        'expiration_date':
        expiration_date,
        'minimum_trust_server':
        minimum_trust,
        'minimum_trust_client':
        minimum_trust,
        'requester_accuracy_target':
        minimum_trust,
        'recording_oracle_addr':
        REC_ORACLE,
        'reputation_oracle_addr':
        REP_ORACLE,
        'reputation_agent_addr':
        REP_ORACLE,
        'instant_result_delivery_webhook':
        CALLBACK_URL,
        'requester_question': {
            "en": "How much money are we to make"
        },
        'requester_question_example':
        FAKE_URL,
        'job_total_tasks':
        number_of_tasks,
        'taskdata_uri':
        FAKE_URL
    })
    manifest.validate()
    return manifest


class ContractTest(unittest.TestCase):
    # TODO bid amount should require positive values,
    # expiration date should require a reasonable date
    # i.e. this test should fai
    def test_basic_construction(self):
        a_manifest()

    def test_can_fail_toconstruct(self):
        # TODO Should fail
        a_manifest(-1)
        self.assertRaises(schematics.exceptions.DataError, a_manifest,
                          "invalid amount")

    def test_can_fail_toconstruct2(self):
        mani = a_manifest()
        mani.taskdata_uri = 'test'
        self.assertRaises(schematics.exceptions.DataError, mani.validate)


class LocalBlockchainTest(unittest.TestCase):
    def setUp(self):
        self.manifest = a_manifest()
        self.contract = api.Contract(self.manifest)
        self.amount = 1000

    def test_contract_needs_funding(self):
        # We shouldn't test this on our internal blockchain because it's slow
        manifest = REQ_JSON
        contract = api.get_job()
        self.assertFalse(
            api.setup_job(contract, self.amount, manifest, Web3.toBytes(0)))

    def test_create_start_contract(self):
        # We shouldn't test this on our internal blockchain because it's slow
        manifest = REQ_JSON

        contract = api.get_job()
        self.assertTrue(
            api._transfer_to_contract(contract.address, self.amount))
        self.assertTrue(
            api.setup_job(contract, self.amount, manifest, Web3.toBytes(0)))
        self.assertEqual(api._balance(contract), self.amount)

    def test_intermediate_results(self):
        # We shouldn't test this on our internal blockchain because it's slow
        manifest = REQ_JSON

        contract = api.get_job()
        self.assertTrue(
            api._transfer_to_contract(contract.address, self.amount))
        self.assertTrue(
            api.setup_job(contract, self.amount, manifest, Web3.toBytes(0)))
        api.store_results(contract, manifest, "0")
        self.assertEquals(manifest, api._getIURL(contract))

    def test_create_start_contract_spend_to_complete(self):
        # We shouldn't test this on our internal blockchain because it's slow
        manifest = REQ_JSON
        contract = api.get_job()
        self.assertTrue(
            api._transfer_to_contract(contract.address, self.amount))
        self.assertTrue(
            api.setup_job(contract, self.amount, manifest, Web3.toBytes(0)))
        self.assertEqual(api._balance(contract), self.amount)
        to_address = TO_ADDR
        api.partial_payout(contract, self.amount, to_address, manifest,
                           Web3.toBytes(0))
        self.assertEquals(manifest, api._getFURL(contract))

    def test_create_start_contract_spend_to_oracle_fees(self):
        manifest = REQ_JSON
        escrow = api.get_job()
        address = ADDR
        address_balance = escrow.call().getAddressBalance(address)
        to_address = TO_ADDR
        to_address_balance = escrow.call().getAddressBalance(to_address)

        self.assertTrue(api._transfer_to_contract(escrow.address, self.amount))

        address_balance_after_transfer = escrow.call().getAddressBalance(
            address)
        self.assertEqual(address_balance_after_transfer,
                         address_balance - 1000)

        self.assertTrue(
            api.setup_job(escrow, self.amount, manifest, Web3.toBytes(0)))
        self.assertEqual(api._balance(escrow), self.amount)
        api.partial_payout(escrow, self.amount, to_address, manifest,
                           Web3.toBytes(0))

        address_balance_after_payout = escrow.call().getAddressBalance(address)

        # Stake has been set to 5% which in these tests is 50.
        # 100 is the correct fee because our address is both the reputation and recording oracle.
        self.assertEqual(address_balance_after_payout,
                         address_balance_after_transfer + 100)

        to_address_balance_after_payout = escrow.call().getAddressBalance(
            to_address)
        self.assertEqual(to_address_balance_after_payout,
                         to_address_balance + 900)

    def test_oo(self):
        to_address = TO_ADDR
        self.assertTrue(self.contract.deploy(PUB2, PRIV1))
        self.assertEqual(self.contract.status(), api.Status.Launched)
        contract_address = self.contract.job_contract.address
        self.assertTrue(self.contract.fund())
        self.assertEqual(self.contract.status(), api.Status.Launched)
        self.assertTrue(self.contract.launch())
        self.assertEqual(self.contract.status(), api.Status.Pending)
        contract2 = api.get_contract_from_address(contract_address, PRIV2)
        self.assertNotEqual({}, contract2.get_manifest(PRIV2))
        contract2.store_intermediate({}, PUB1, PRIV2)
        self.assertEqual({}, contract2.get_intermediate_results(PRIV1))

        self.assertEqual(self.contract.status(), api.Status.Pending)

        amount_to_payout = 1
        contract2.payout(amount_to_payout, to_address, {}, PUB2, PRIV1)
        self.assertEqual(self.contract.status(), api.Status.Partial)
        self.assertFalse(contract2.complete())
        self.assertEqual({}, contract2.get_results(PRIV2))

        amount_to_payout = contract2.amount - amount_to_payout
        contract2.payout(amount_to_payout, to_address, {}, PUB2, PRIV1)
        self.assertEqual(self.contract.status(), api.Status.Paid)
        self.assertTrue(contract2.complete())
        self.assertEqual(self.contract.status(), api.Status.Complete)


class EncryptionTest(unittest.TestCase):
    def test_encryption_decryption_identity(self):
        plaintext = 'asdfasdf'
        cipher = _encrypt(PUB2, plaintext)
        self.assertEqual(_decrypt(PRIV2, cipher), plaintext)


def add_bytes(args):
    pass


def encrypt(public_key, msg):
    pass


class StorageTest(unittest.TestCase):
    @patch('api.storage.API.add_bytes', side_effect=add_bytes)
    @patch('api.storage._encrypt', side_effect=encrypt)
    def test_upload(self, add_bytes, _encrypt):
        upload(a_manifest().serialize(), PUB1)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.INFO)
    unittest.main()
