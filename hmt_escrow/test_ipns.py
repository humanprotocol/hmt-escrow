import unittest
from unittest.mock import patch 
import random 
from basemodels import Manifest

from storage import download, upload, get_ipns_link, create_new_ipns_link, _connect, IPFS_CLIENT, ipns_link_exists
from job import Job

import pdb; 

# logging = print
logging = lambda *argv: None

class MockIpns():
    def __init__(self):
        # Hidden state
        self._id   = None
        self._name = None
        self._data = None
        self._hash = None

    def key_gen(self, name, key_type):
        self._id = str(random.getrandbits(32))
        self._name = name
        logging('>>>> key_gen',self._id, name)


    def key_list(self): 
        ret = {'Keys': [{'Name': self._name, 'Id': self._id}]}
        logging('>>>> key_list', ret)
        return ret

    def add_bytes(self, data): 
        logging('>>>> add_bytes')
        self._data = data
        rnd = f'Q{str(random.getrandbits(32))}'
        self._hash = f'Q{rnd}'
        return self._hash
    
    def publish(self, path, key='', allow_offline=False): 
        logging('>>>> publish', self._hash, path.split('/')[-1])
        _hash = path.split('/')[-1]
        assert(_hash == self._hash)
        self._name = key

    def resolve(self, ipns_path):
        logging('>>>> resolve', ipns_path)
        assert(ipns_path.split('/')[-1] == self._id)
        return {'Path': f'_/{self._hash}'}

    def cat(self, _hash):
        logging('>>>> cat', _hash)
        assert(_hash == self._hash)
        return self._data

MI = MockIpns()

# setUp, runs before every test function. 
# tearDown, common teardown fn
class IpnsTest(unittest.TestCase):
    '''
    Tests storage functions by mocking ipfs/ipns
    '''


    # @patch('storage.IPFS_CLIENT.key.gen')
    @patch('storage._connect')
    @patch('storage.IPFS_CLIENT')
    def test_ipns(self, mocked_ipfs_client, _):
        """
        Test storage: upload, download, create_new_ipns_link, etc
        """

        credentials = {
            "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
            "gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        }
        pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        job = Job(credentials=credentials, escrow_manifest=Manifest({'task_bid_price': 9, 'request_type': 'image_label_binary', 'job_total_tasks': 10}))
        name = 'abc'

        mocked_ipfs_client.key.list.side_effect = MI.key_list
        mocked_ipfs_client.key.gen.side_effect = MI.key_gen
        mocked_ipfs_client.name.publish.side_effect = MI.publish
        mocked_ipfs_client.add_bytes.side_effect = MI.add_bytes
        mocked_ipfs_client.resolve.side_effect = MI.resolve
        mocked_ipfs_client.cat.side_effect = MI.cat

        # Test
        ipns_id = create_new_ipns_link(name)
        (hash_, manifest_url) = upload(job.serialized_manifest, pub_key, name)
        manifest_dict = download(ipns_id, job.gas_payer_priv)
        dl_equals_up = manifest_dict == job.serialized_manifest
        link_exist = ipns_link_exists(name)
        ipns_urls_match = ipns_id == get_ipns_link(name).split('/')[-1]

        # Asserts
        self.assertTrue(dl_equals_up)
        self.assertTrue(link_exist)
        self.assertTrue(ipns_urls_match)

if __name__ == '__main__':
    unittest.main()
