import unittest
import mock
# from mock import patch

class IpnsTest(unittest.TestCase):
    '''
    Tests storage functions by mocking ipfs/ipns
    '''

    @mock.patch('IPFS_CLIENT.key.gen')
    @mock.patch('IPFS_CLIENT.cat')
    @mock.patch('IPFS_CLIENT.name.resolve')
    @mock.patch('IPFS_CLIENT.name.publish')
    @mock.patch('IPFS_CLIENT.add_bytes')
    def test_ipns(self, mock_ipfs_add_bytes, mock_ipfs_publish, mock_ipns_resolve, mock_ipfs_cat, mock_ipfs_cat):
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

        ipns_url = create_new_ipns_link('name')

        (hash_, manifest_url) = upload(job.serialized_manifest, pub_key, name)
        manifest_dict         = download(None, job.gas_payer_priv, name)

        self.assertTrue(manifest_dict == job.serialized_manifest)
        self.assertTrue(ipns_link_exists(name))
        self.assertTrue(ipns_url == get_ipns_link(name))
