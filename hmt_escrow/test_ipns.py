import unittest
import mock
import random 

class MockIpns:
    def __init__():
        # Hidden state
        self._id   = None
        self._name = None
        self._data = None
        self._hash = None

    def key_gen(name, key_type):
        self._name = name
        self._id = str(random.getrandbits(32 * 8))

    def key_list(): 
        return {'Id': self._id, 'Keys': [{'Name': self._name}]}

    def add_bytes(data): 
        self._data = data
        self._hash = f'Q{str(random.getrandbits(32 * 8))}'
        return f'hash{self._hash}'

    def publish(path, name, _): 
        _hash = path.split('/')[-1]
        assert(_hash == self._hash)
        self._name = name 

    def resolve(ipns_path):
        assert(ipns_path.split('/')[-1] == self._id)
        return [{'Path': f'_/{self._path}'}]

    def cat():
        return _data


class IpnsTest(unittest.TestCase):
    '''
    Tests storage functions by mocking ipfs/ipns
    '''
    def __init__(): 
        self.mi = MockIpns()
    
    @mock.patch('IPFS_CLIENT.key.gen'     , side_effect=self.mi.key_gen)
    @mock.patch('IPFS_CLIENT.cat'         , side_effect=self.mi.cat)
    @mock.patch('IPFS_CLIENT.resolve'     , side_effect=self.mi.resolve)
    @mock.patch('IPFS_CLIENT.name.publish', side_effect=self.mi.publish)
    @mock.patch('IPFS_CLIENT.add_bytes'   , side_effect=self.mi.add_bytes)
    @mock.patch('IPFS_CLIENT.key.list'    , side_effect=self.mi.key_list)
    def test_ipns(self, mock_ipfs_key_list, mock_ipfs_add_bytes, mock_ipfs_publish, mock_ipns_resolve, mock_ipfs_cat, mock_ipfs_key_gen):
        """
        Test storage: upload, download, create_new_ipns_link, etc
        """
        credentials = {
            "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
            "gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        }
        pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        job = Job(credentials=credentials, escrow_manifest=manifest)
        name = 'abc'

        # Test
        ipns_url = create_new_ipns_link('name')
        (hash_, manifest_url) = upload(job.serialized_manifest, pub_key, name)
        manifest_dict = download(None, job.gas_payer_priv, name)
        dl_equals_up = manifest_dict == job.serialized_manifest
        link_exist = ipns_link_exists(name)
        ipns_urls_match = ipns_url == get_ipns_link(name)

        # Asserts
        self.assertTrue(dl_equals_up)
        self.assertTrue(link_exist)
        self.assertTrue(ipns_urls_match)
