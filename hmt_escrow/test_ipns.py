import unittest
import logging
import mock
from mock import patch
from basemodels import Manifest
from loader.entry import runner
from loader.blockchain import load_job_blockchain
from common_helpers import mocked_exchange_post, load_fake_manifest, mock_job, mock_get_pk_from_address, set_up_blockchain_config


class IpnsTest(unittest.TestCase):
    '''
    1) apply patch on X, 
    2) call function that in turn calls X within that test, 
    3) get an object back and take a look at all the things 
       that X should have been called with /etc
    '''

    @mock.patch('IPFS_CLIENT.add_bytes')
    def test_upload(self, mock_ipfs_add_bytes):
        """
        Tests that upload works, replace ipfs fn
        """
        
    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials=credentials, escrow_manifest=manifest)
    >>> (hash_, manifest_url) = upload(job.serialized_manifest, pub_key)
    >>> manifest_dict = download(manifest_url, job.gas_payer_priv)
    >>> manifest_dict == job.serialized_manifest
    True
        

        def upload(msg: Dict, public_key: bytes, ipns_keypair_name: str) -> Tuple[str, str]:
        upload({})
        self.assertTrue(mock_ipfs_add_bytes.called)
        data = mock_ipfs_add_bytes.call_args[0][0].to_primitive()

        self.assertIn('job_id', data)


    @mock.patch('download')
    def test_download(self, mock_download):
        download
        
    '''
    def download(key: str, private_key: bytes) -> Dict:
    def create_new_ipns_link(name: str) -> str:
    def get_ipns_link(name: str) -> str:
    def upload(msg: Dict, public_key: bytes, ipns_keypair_name: str='') -> Tuple[str, str]:
    '''

