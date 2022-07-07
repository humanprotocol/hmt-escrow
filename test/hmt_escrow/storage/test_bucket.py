import unittest
from unittest.mock import patch

from hmt_escrow.storage import get_bucket, get_public_bucket_url, get_key_from_url

ESCROW_TEST_BUCKETNAME = "test-escrow-results"
ESCROW_TEST_PUBLIC_BUCKETNAME = "test-escrow-public-results"

ESCROW_TEST_PUBLIC_RESULTS_URL = 'http://my-public-bucket.s3.amazon.com'


class BucketTest(unittest.TestCase):
    """ Bucket related tests """

    @patch("hmt_escrow.storage.ESCROW_BUCKETNAME", ESCROW_TEST_BUCKETNAME)
    def test_retrieving_internal_bucket(self):
        """ Tests whether internal bucket is retrieved as a non-public bucket. """
        bucket_name = get_bucket(public=False)
        self.assertEqual(bucket_name, ESCROW_TEST_BUCKETNAME)

    @patch("hmt_escrow.storage.ESCROW_PUBLIC_BUCKETNAME", ESCROW_TEST_PUBLIC_BUCKETNAME)
    def test_retrieving_public_bucket(self):
        """ Tests whether public bucket is retrieved as a public bucket. """
        bucket_name = get_bucket(public=True)
        self.assertEqual(bucket_name, ESCROW_TEST_PUBLIC_BUCKETNAME)

    @patch("hmt_escrow.storage.ESCROW_PUBLIC_RESULTS_URL", ESCROW_TEST_PUBLIC_RESULTS_URL)
    def test_public_bucket_url_retrieval(self):
        """ Tests whether bucket public URL is retrieved correctly. """
        key = 's3aaa'
        expected_url = f'{ESCROW_TEST_PUBLIC_RESULTS_URL}/{key}'

        url = get_public_bucket_url(key)
        self.assertEqual(url, expected_url)

    def test_key_retrieval_from_file_url(self):
        """ Testes whether key can be retrieved from URL correctly. """
        expected_key = 's3aaa'

        # Qualified URL must be parsed and key retrieved
        url = f'{ESCROW_TEST_PUBLIC_RESULTS_URL}/{expected_key}'
        key = get_key_from_url(url)
        self.assertEqual(key, expected_key)

        # Key passed as URL without qualification must return key
        key = get_key_from_url(key)
        self.assertEqual(key, expected_key)


if __name__ == "__main__":
    unittest.main(exit=True)
