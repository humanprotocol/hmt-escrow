#!/usr/bin/env python3

import logging
import os
import sys
import unittest
from decimal import *

from unittest.mock import MagicMock, ANY
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
TO_ADDR2 = '0xa30E4681db25f0f32E8C79b28F2A80A653A556A2'

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
               bid_amount=1.0,
               oracle_stake=0.05,
               expiration_date=0,
               minimum_trust=.1,
               request_type=IMAGE_LABEL_BINARY,
               request_config=None,
               job_mode='batch') -> basemodels.Manifest:
    model = {
        'requester_restricted_answer_set': {
            '0': {
                'en': 'English Answer 1'
            },
            '1': {
                'en': 'English Answer 2',
                'answer_example_uri':
                'https://hcaptcha.com/example_answer2.jpg'
            }
        },
        'job_mode': job_mode,
        'request_type': request_type,
        'unsafe_content': False,
        'task_bid_price': bid_amount,
        'oracle_stake': oracle_stake,
        'expiration_date': expiration_date,
        'minimum_trust_server': minimum_trust,
        'minimum_trust_client': minimum_trust,
        'requester_accuracy_target': minimum_trust,
        'recording_oracle_addr': REC_ORACLE,
        'reputation_oracle_addr': REP_ORACLE,
        'reputation_agent_addr': REP_ORACLE,
        'instant_result_delivery_webhook': CALLBACK_URL,
        'requester_question': {
            "en": "How much money are we to make"
        },
        'requester_question_example': FAKE_URL,
        'job_total_tasks': number_of_tasks,
        'taskdata_uri': FAKE_URL
    }

    if request_config:
        model.update({'request_config': request_config})

    manifest = basemodels.Manifest(model)
    manifest.validate()

    return manifest


class ContractTest(unittest.TestCase):
    """
    Tests the escrow API's functions.

    Some of the blockchain specific functionality is mocked.
    Contract specific functionality is delegated to JS tests.
    """

    def setUp(self):
        """Set up the fields for Contract class testing, based on the test manifest."""
        self.manifest = a_manifest()
        self.contract = api.Contract(self.manifest)
        self.per_job_cost = Decimal(self.manifest['task_bid_price'])
        self.total_tasks = self.manifest['job_total_tasks']
        self.oracle_stake = self.manifest['oracle_stake']
        self.amount = (self.per_job_cost * self.total_tasks) * 10**18

    def test_basic_construction(self):
        """Tests that manifest can validate the test manifest properly."""
        a_manifest()

    def test_can_fail_toconstruct(self):
        """Tests that the manifest raises an Error when called with falsy parameters."""
        a_manifest(-1)
        self.assertRaises(schematics.exceptions.DataError, a_manifest,
                          "invalid amount")

    def test_can_fail_toconstruct2(self):
        """Tests that validated fields can't be broken without an exception."""
        mani = a_manifest()
        mani.taskdata_uri = 'test'
        self.assertRaises(schematics.exceptions.DataError, mani.validate)

    def test_can_make_request_config_job(self):
        """Test that jobs with valid request_config parameter work"""
        manifest = a_manifest(
            request_type='image_label_area_select',
            request_config={'shape_type': 'point'})

    def test_can_bad_request_config(self):
        """Test that an invalid shape_type in request_config will fail"""
        manifest = a_manifest()
        manifest.request_type = 'image_label_area_select'
        manifest.request_config = {'shape_type': 'not-a-real-option'}
        self.assertRaises(schematics.exceptions.DataError, manifest.validate)

    def test_initialize(self):
        """Tests that initialize gets called with correct parameters inside contract.deploy."""
        self.contract.initialize = MagicMock()
        self.contract.deploy(PUB2, PRIV1)
        self.contract.initialize.assert_called_once_with(
            ANY, self.amount, self.oracle_stake, self.total_tasks)

    def test_deploy(self):
        """Tests that deploy assigns correct field values to Contract class state."""
        self.contract.deploy(PUB2, PRIV1)
        self.assertEqual(self.contract.amount, self.amount)
        self.assertEqual(self.contract.oracle_stake, self.oracle_stake)
        self.assertEqual(self.contract.number_of_answers, self.total_tasks)

    def test_fund(self):
        """Tests that fund calls _transfer_to_address with correct parameters."""
        api._transfer_to_address = MagicMock()
        self.contract.deploy(PUB2, PRIV1)
        self.contract.fund()
        api._transfer_to_address.assert_called_once_with(
            self.contract.job_contract.address, self.amount)

    def test_abort(self):
        """Tests that abort calls _abort_sol with correct parameters."""
        api._abort_sol = MagicMock()
        self.contract.deploy(PUB2, PRIV1)
        self.contract.abort()
        api._abort_sol.assert_called_once_with(self.contract.job_contract, ANY)

    def test_complete(self):
        """Tests that complete calls _complete with correct parameters."""
        api._complete = MagicMock()
        self.contract.deploy(PUB2, PRIV1)
        self.contract.complete()
        api._complete.assert_called_once_with(self.contract.job_contract)

    def test_launch(self):
        """Tests that launch calls _setup_sol with correct parameters."""
        api._setup_sol = MagicMock()
        self.contract.deploy(PUB2, PRIV1)
        self.contract.launch()
        api._setup_sol.assert_called_once_with(
            self.contract.job_contract, ANY, ANY, self.oracle_stake,
            self.oracle_stake, self.amount, self.contract.manifest_url,
            self.contract.manifest_hash)

    def test_store_intermediate(self):
        """Tests that store_intermediate calls _store_results without parameters."""
        api._store_results = MagicMock()
        self.contract.deploy(PUB2, PRIV1)
        self.contract.store_intermediate({}, PUB2, PRIV1)
        api._store_results.assert_called_once()

    def test_refund(self):
        """Tests that refund calls _refund_sol with correct parameters."""
        api._refund_sol = MagicMock()
        self.contract.deploy(PUB2, PRIV1)
        self.contract.refund()
        api._refund_sol.assert_called_once_with(self.contract.job_contract,
                                                ANY)

    def test_payout(self):
        """Tests that payout calls _partial_payout with correct amount after HMT decimal conversion."""
        api._partial_payout_sol = MagicMock()
        self.contract.deploy(PUB2, PRIV1)
        amount = 10
        self.contract.payout(amount, TO_ADDR, {}, PUB2, PRIV1)
        assert_amount = 10 * 10**18
        api._partial_payout_sol.assert_called_once_with(
            self.contract.job_contract, assert_amount, TO_ADDR, ANY, ANY)

    def test_bulk_payout(self):
        """Tests that bulk_payout calls _bulk_payout with correct amounts after HMT decimal conversion."""
        api._bulk_payout_sol = MagicMock()
        self.contract.deploy(PUB2, PRIV1)
        addresses = [TO_ADDR, TO_ADDR2]
        amounts = [10, 20]
        self.contract.bulk_payout(addresses, amounts, {}, PUB2, PRIV1)
        assert_amounts = [10 * 10**18, 20 * 10**18]
        api._bulk_payout_sol.assert_called_once_with(
            self.contract.job_contract, addresses, assert_amounts, ANY, ANY)


class EncryptionTest(unittest.TestCase):
    def test_encryption_decryption_identity(self):
        """Tests _decrypt of _encrypt message returns the same message."""
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
    logging.basicConfig()
    logging.getLogger("urllib3").setLevel(logging.INFO)
    unittest.main()
