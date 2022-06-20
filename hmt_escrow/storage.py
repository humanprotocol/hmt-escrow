import hashlib
import json
import logging
import os
from typing import Dict, Tuple

import boto3

from hmt_escrow import crypto

SHARED_MAC_DATA: bytes = os.getenv(
    "SHARED_MAC", "9da0d3721774843193737244a0f3355191f66ff7321e83eae83f7f746eb34350"
).encode("ascii")

logging.getLogger("boto").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("boto3").setLevel(logging.INFO)

DEBUG = "true" in os.getenv("DEBUG", "false").lower()
LOG = logging.getLogger("hmt_escrow.storage")
LOG.setLevel(logging.DEBUG if DEBUG else logging.INFO)

ESCROW_BUCKETNAME = os.getenv("ESCROW_BUCKETNAME", "escrow-results")
ESCROW_AWS_ACCESS_KEY_ID = os.getenv("ESCROW_AWS_ACCESS_KEY_ID", "minio")
ESCROW_AWS_SECRET_ACCESS_KEY = os.getenv("ESCROW_AWS_SECRET_ACCESS_KEY", "minio123")
ESCROW_AWS_REGION = os.getenv("ESCROW_AWS_REGION", "us-west-2")
ESCROW_ENDPOINT_URL = os.getenv("ESCROW_ENDPOINT_URL", "http://minio:9000")


def _connect_s3():
    try:
        return boto3.client(
            "s3",
            aws_access_key_id=ESCROW_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=ESCROW_AWS_SECRET_ACCESS_KEY,
            endpoint_url=ESCROW_ENDPOINT_URL,
            region_name=ESCROW_AWS_REGION,
        )
    except Exception as e:
        LOG.error(f"Connection with S3 failed because of: {e}")
        raise e


def download(key: str, private_key: bytes) -> Dict:
    """Download a key, decrypt it, and output it as a binary string.

    Args:
        key (str): This is the hash code returned when uploading.
        private_key (str): The private_key to decrypt this string with.

    Returns:
        Dict: returns the contents of the filename which was previously uploaded.

    Raises:
        Exception: if reading from fails.

    """
    try:
        LOG.debug("Downloading s3 key: {}".format(key))
        BOTO3_CLIENT = _connect_s3()
        response = BOTO3_CLIENT.get_object(Bucket=ESCROW_BUCKETNAME, Key=key)
        ciphertext = response["Body"].read()
        msg = crypto.decrypt(private_key, ciphertext)
    except Exception as e:
        LOG.warning(
            "Reading the key {!r} with private key {!r} with S3 failed because of: {!r}".format(
                key, private_key, e
            )
        )
        raise e
    return json.loads(msg)


def upload(msg: Dict, public_key: bytes) -> Tuple[str, str]:
    """Upload and encrypt a string for later retrieval.
    This can be manifest files, results, or anything that's been already
    encrypted.

    Args:
        msg (Dict): The message to upload and encrypt.
        public_key (bytes): The public_key to encrypt the file for.

    Returns:
        Tuple[str, str]: returns the contents of the filename which was previously uploaded.

    Raises:
        Exception: if adding bytes fails.

    """
    try:
        manifest_ = json.dumps(msg, sort_keys=True)
    except Exception as e:
        LOG.error("Can't extract the json from the dict")
        raise e

    hash_ = hashlib.sha1(manifest_.encode("utf-8")).hexdigest()

    BOTO3_CLIENT = _connect_s3()
    encrypted_msg = crypto.encrypt(public_key, manifest_)
    key = f"s3{hash_}"
    BOTO3_CLIENT.put_object(Bucket=ESCROW_BUCKETNAME, Key=key, Body=encrypted_msg)
    LOG.debug(f"Uploaded to S3, key: {key}")
    return hash_, key
