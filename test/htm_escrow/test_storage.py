import logging
import os
import unittest

from hmt_escrow import crypto
from hmt_escrow.storage import upload, download, _encrypt, _decrypt
from hmt_escrow.job import Job

from test.htm_escrow.utils import manifest

SHARED_MAC_DATA: bytes = os.getenv(
    "SHARED_MAC",
    "9da0d3721774843193737244a0f3355191f66ff7321e83eae83f7f746eb34350"
).encode("ascii")

logging.getLogger("boto").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("boto3").setLevel(logging.INFO)


class StorageTest(unittest.TestCase):
    def test_download(self):
        credentials = {
            "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
            "gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        }
        pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        job = Job(credentials=credentials, escrow_manifest=manifest)
        (_, manifest_url) = upload(job.serialized_manifest, pub_key)
        manifest_dict = download(manifest_url, job.gas_payer_priv)
        self.assertEqual(manifest_dict, job.serialized_manifest)

        job = Job(credentials=credentials, escrow_manifest=manifest)
        (_, manifest_url) = upload(job.serialized_manifest, pub_key)
        manifest_dict = download(manifest_url, job.gas_payer_priv)
        self.assertEqual(manifest_dict, job.serialized_manifest)

    def test_upload(self):
        credentials = {
            "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
            "gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        }
        pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        job = Job(credentials=credentials, escrow_manifest=manifest)
        (_, manifest_url) = upload(job.serialized_manifest, pub_key)
        manifest_dict = download(manifest_url, job.gas_payer_priv)
        self.assertEqual(manifest_dict, job.serialized_manifest)

        job = Job(credentials=credentials, escrow_manifest=manifest)
        (_, manifest_url) = upload(job.serialized_manifest, pub_key)
        self.assertTrue(manifest_url.startswith("s3"))
        manifest_dict = download(manifest_url, job.gas_payer_priv)
        self.assertEqual(manifest_dict, job.serialized_manifest)

    def test_decrypt(self):
        priv_key = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        msg = "test"
        self.assertEqual(_decrypt(priv_key, _encrypt(pub_key, msg)), msg)
        # Using a wrong public key to decrypt a message results in failure.
        false_pub_key = b"74c81fe41b30f741b31185052664a10c3256e2f08bcfb20c8f54e733bef58972adcf84e4f5d70a979681fd39d7f7847d2c0d3b5d4aead806c4fec4d8534be114"
        with self.assertRaises(crypto.DecryptionError):
            _decrypt(priv_key, _encrypt(false_pub_key, msg)) == msg

    def test_encrypt(self):
        priv_key = b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        msg = "test"
        self.assertEqual(_decrypt(priv_key, _encrypt(pub_key, msg)), msg)


if __name__ == "__main__":
    unittest.main(exit=True)
