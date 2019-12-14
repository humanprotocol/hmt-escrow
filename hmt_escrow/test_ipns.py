import unittest
from unittest.mock import patch
import random
from basemodels import Manifest

from storage import download, upload, get_ipns_link, create_new_ipns_link, _connect, IPFS_CLIENT, ipns_link_exists
from job import Job

import pdb

# logging = print
logging = lambda *argv: None


class MockIpns():
    def __init__(self):
        # Hidden state
        self.ipns_id_to_hash = {'id123': 'hash123'}
        self.ipns_name_to_id = {'name123': 'id123'}
        self.ipns_hash_to_data = {'hash123': 'data123'}

    def key_gen(self, name, key_type):
        _id = str(random.getrandbits(32))
        self.ipns_id_to_hash[_id] = None
        self.ipns_name_to_id[name] = _id
        logging('>>>> key_gen', _id, name)

    def key_list(self):
        # ret = {'Keys': [{'Name': self._name, 'Id': self._id}]}
        ret = {
            'Keys': [{
                'Name': name,
                'Id': self.ipns_name_to_id[name]
            } for name in self.ipns_name_to_id if True]
        }
        logging('>>>> key_list', ret)
        return ret

    def add_bytes(self, data):
        logging('>>>> add_bytes')
        _hash = f'Q{100000000000000000000+hash(str(data))}'  # get positive int
        self.ipns_hash_to_data[_hash] = data
        return _hash

    # TODO: if key='', then should be on last ipns id setup, i.e. last time key_gen was called
    def publish(self, path, key='', allow_offline=False):
        _hash = path.split('/')[-1]
        _id = self.ipns_name_to_id[key]
        self.ipns_id_to_hash[_id] = _hash
        logging('>>>> publish', path, key, _hash)

    def resolve(self, ipns_path):
        ipns_id = ipns_path.split('/')[-1]
        _hash = self.ipns_id_to_hash[ipns_id]
        logging('>>>> resolve', ipns_id, _hash)
        return {'Path': f'_/{_hash}'}

    def cat(self, _hash):
        logging('>>>> cat', _hash)
        return self.ipns_hash_to_data[_hash]


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
            "gas_payer":
            "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
            "gas_payer_priv":
            "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        }
        pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        job = Job(credentials=credentials,
                  escrow_manifest=Manifest({
                      'task_bid_price': 9,
                      'request_type': 'image_label_binary',
                      'job_total_tasks': 10
                  }))
        name = 'abc'

        mocked_ipfs_client.key.list.side_effect = MI.key_list
        mocked_ipfs_client.key.gen.side_effect = MI.key_gen
        mocked_ipfs_client.name.publish.side_effect = MI.publish
        mocked_ipfs_client.add_bytes.side_effect = MI.add_bytes
        mocked_ipfs_client.resolve.side_effect = MI.resolve
        mocked_ipfs_client.cat.side_effect = MI.cat

        ipns_id = create_new_ipns_link(name)

        # Upload 1
        (hash_, manifest_url) = upload(job.serialized_manifest, pub_key, name)
        manifest_dict = download(ipns_id, job.gas_payer_priv)
        dl_equals_up = manifest_dict == job.serialized_manifest
        link_exist = ipns_link_exists(name)
        ipns_urls_match = ipns_id == get_ipns_link(name).split('/')[-1]
        self.assertTrue(dl_equals_up)
        self.assertTrue(link_exist)
        self.assertTrue(ipns_urls_match)

        # Upload 2
        data2 = dict(
            Manifest({
                'task_bid_price': 999999,
                'request_type': 'image_label_binary',
                'job_total_tasks': 30010
            }).serialize())
        (hash_, manifest_url) = upload(data2, pub_key, name)
        manifest_dict = download(ipns_id, job.gas_payer_priv)
        dl_equals_up = manifest_dict == data2
        link_exist = ipns_link_exists(name)
        ipns_urls_match = ipns_id == get_ipns_link(name).split('/')[-1]
        self.assertTrue(dl_equals_up)
        self.assertTrue(link_exist)
        self.assertTrue(ipns_urls_match)


if __name__ == '__main__':
    unittest.main()
