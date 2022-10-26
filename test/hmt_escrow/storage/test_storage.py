import json
import logging
import unittest
from unittest.mock import MagicMock, patch

from hmt_escrow import crypto
from hmt_escrow.storage import upload, download, download_from_storage
from test.hmt_escrow.utils import test_manifest

ESCROW_TEST_BUCKETNAME = "test-escrow-results"
ESCROW_TEST_PUBLIC_BUCKETNAME = "test-escrow-public-results"

logging.getLogger("boto").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("boto3").setLevel(logging.INFO)


class StorageTest(unittest.TestCase):
    bid_amount = 1.0  # value to be inserted in manifest

    def get_manifest(self) -> dict:
        """Retrieves manifest differing bid amount to bid amount to force unique state of the manifest"""
        manifest = test_manifest(bid_amount=self.bid_amount)
        self.bid_amount += 0.1
        return dict(manifest.serialize())

    def setUp(self) -> None:
        self.pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        self.priv_key = (
            b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        )

    @patch("hmt_escrow.storage.ESCROW_PUBLIC_BUCKETNAME", ESCROW_TEST_PUBLIC_BUCKETNAME)
    @patch("hmt_escrow.storage.ESCROW_BUCKETNAME", ESCROW_TEST_BUCKETNAME)
    def test_upload_to_private_bucket(self):
        """
        Tests uploading file to storage to private bucket when encryption is on.
        """

        s3_client_mock = MagicMock()
        with patch("hmt_escrow.storage._connect_s3") as mock_s3:
            mock_s3.return_value = s3_client_mock

            upload(
                self.get_manifest(),
                self.pub_key,
                encrypt_data=True,
                use_public_bucket=False,
            )

            mock_s3.assert_called()
            self.assertIn("Bucket", s3_client_mock.put_object.call_args.kwargs.keys())

            # With use_public_bucket False, bucket MUST be the private one
            self.assertEqual(
                s3_client_mock.put_object.call_args.kwargs["Bucket"],
                ESCROW_TEST_BUCKETNAME,
            )

    @patch("hmt_escrow.storage.ESCROW_PUBLIC_BUCKETNAME", ESCROW_TEST_PUBLIC_BUCKETNAME)
    def test_upload_to_public_bucket(self):
        """Tests uploading file to storage to public bucket only when encryption is off."""

        s3_client_mock = MagicMock()
        with patch("hmt_escrow.storage._connect_s3") as mock_s3:
            mock_s3.return_value = s3_client_mock

            upload(
                self.get_manifest(),
                self.pub_key,
                encrypt_data=True,
                use_public_bucket=True,
            )

            mock_s3.assert_called()

            self.assertIn("Bucket", s3_client_mock.put_object.call_args.kwargs.keys())

            # With use_public_bucket True, bucket MUST be the public one
            self.assertIn(
                s3_client_mock.put_object.call_args.kwargs["Bucket"],
                ESCROW_TEST_PUBLIC_BUCKETNAME,
            )

    def test_upload_with_enabled_encryption_option(self):
        """
        Tests data persisted in storage is encrypted.
        """
        s3_client_mock = MagicMock()
        with patch("hmt_escrow.storage._connect_s3") as mock_s3:
            mock_s3.return_value = s3_client_mock

            # Encryption on (default).
            data = self.get_manifest()
            upload(data, self.pub_key, encrypt_data=True)

            mock_s3.assert_called()
            self.assertIn("Body", s3_client_mock.put_object.call_args.kwargs.keys())

            # Data to be uploaded must be encrypted
            uploaded_content = crypto.decrypt(
                self.priv_key, s3_client_mock.put_object.call_args.kwargs["Body"]
            )
            self.assertEqual(json.dumps(data, sort_keys=True), uploaded_content)

    def test_upload_with_disabled_encryption_option(self):
        """
        Tests data persisted in storage is plain.
        """
        s3_client_mock = MagicMock()
        with patch("hmt_escrow.storage._connect_s3") as mock_s3:
            mock_s3.return_value = s3_client_mock
            # Encryption off.
            data = self.get_manifest()
            upload(data, self.pub_key, encrypt_data=False)

            mock_s3.assert_called()
            self.assertIn("Body", s3_client_mock.put_object.call_args.kwargs.keys())

            # Data to be uploaded must be plain
            uploaded_content = s3_client_mock.put_object.call_args.kwargs["Body"]
            self.assertEqual(
                json.dumps(data, sort_keys=True), uploaded_content.decode()
            )

    @patch("hmt_escrow.storage.ESCROW_BUCKETNAME", ESCROW_TEST_BUCKETNAME)
    def test_download_from_storage_from_private_bucket(self):
        """Tests download of file artifact from storage from private bucket."""
        # Encrypting data is on (default)
        s3_client_mock = MagicMock()
        with patch("hmt_escrow.storage._connect_s3") as mock_s3:
            mock_s3.return_value = s3_client_mock

            download_from_storage(key="s3aaaa", public=False)

        mock_s3.assert_called()

        # With encryption on, bucket is meant to be the public one
        self.assertEqual(
            s3_client_mock.get_object.call_args.kwargs["Bucket"], ESCROW_TEST_BUCKETNAME
        )

    @patch("hmt_escrow.storage.ESCROW_PUBLIC_BUCKETNAME", ESCROW_TEST_PUBLIC_BUCKETNAME)
    def test_download_from_storage_public_bucket(self):
        """Tests download of file artifact from storage from private bucket."""
        s3_client_mock = MagicMock()
        with patch("hmt_escrow.storage._connect_s3") as mock_s3:
            mock_s3.return_value = s3_client_mock

            download_from_storage(key="s3aaaa", public=True)

        mock_s3.assert_called()

        # With encryption on, bucket is meant to be the public one
        self.assertEqual(
            s3_client_mock.get_object.call_args.kwargs["Bucket"],
            ESCROW_TEST_PUBLIC_BUCKETNAME,
        )

    def test_download_from_storage_private_bucket(self):
        """Tests download from storage with encryption on/off and private bucket"""

        # Upload with encryption on (default)
        data = self.get_manifest()
        _, manifest_url = upload(
            data, self.pub_key, encrypt_data=True, use_public_bucket=False
        )
        # Encryption on (default) determines that data is not public
        content = download_from_storage(key=manifest_url, public=False)
        # As encryption is on, let's decrypt
        decrypted = crypto.decrypt(self.priv_key, content)
        self.assertEqual(json.loads(decrypted), data)

        # Upload with encryption off
        data = self.get_manifest()
        _, manifest_url = upload(
            data, self.pub_key, encrypt_data=False, use_public_bucket=False
        )
        # Encryption off determines that data is public
        content = download_from_storage(key=manifest_url, public=False)
        # As encryption is off, data is plain
        self.assertEqual(json.loads(content), data)

    def test_public_private_download_from_storage(self):
        """Tests whether download is correctly called using public or private parameter."""
        file_key = "s3aaa"
        sample_data = '{"a": 1, "b": 2}'

        with patch("hmt_escrow.storage.download_from_storage") as download_mock:
            # 2 returns. 1. encrypted and other plain
            download_mock.side_effect = [
                crypto.encrypt(self.pub_key, sample_data),
                sample_data.encode("utf-8"),
            ]

            # Encryption is on (default)
            downloaded = download(key=file_key, private_key=self.priv_key, public=False)
            self.assertEqual(json.dumps(downloaded), sample_data)

            # Download from storage must be called as PRIVATE (public is FALSE)
            download_mock.assert_called_once_with(key=file_key, public=False)

            download_mock.reset_mock()

            # Encryption is on (default)
            downloaded = download(key=file_key, private_key=self.priv_key, public=True)
            self.assertEqual(json.dumps(downloaded), sample_data)

            # Download from storage must be called as PRIVATE (public is TRUE)
            download_mock.assert_called_once_with(key=file_key, public=True)


if __name__ == "__main__":
    unittest.main(exit=True)
