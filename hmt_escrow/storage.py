import hashlib
import json
import logging
import os
from typing import Dict, Optional, Tuple

import boto3

from hmt_escrow import crypto

SHARED_MAC_DATA: bytes = os.getenv(
    "SHARED_MAC",
    "9da0d3721774843193737244a0f3355191f66ff7321e83eae83f7f746eb34350"
).encode("ascii")

logging.getLogger("boto").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("boto3").setLevel(logging.INFO)

DEBUG = "true" in os.getenv("DEBUG", "false").lower()
LOG = logging.getLogger("hmt_escrow.storage")
LOG.setLevel(logging.DEBUG if DEBUG else logging.INFO)

ESCROW_BUCKETNAME = os.getenv("ESCROW_BUCKETNAME", "escrow-results")
ESCROW_AWS_ACCESS_KEY_ID = os.getenv("ESCROW_AWS_ACCESS_KEY_ID", "minio")
ESCROW_AWS_SECRET_ACCESS_KEY = os.getenv("ESCROW_AWS_SECRET_ACCESS_KEY",
                                         "minio123")
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


def download_from_storage(key: str) -> bytes:
    """ Downloads data from storage if exists. """
    LOG.debug("Downloading s3 key: {}".format(key))

    BOTO3_CLIENT = _connect_s3()
    response = BOTO3_CLIENT.get_object(Bucket=ESCROW_BUCKETNAME, Key=key)
    return response["Body"].read()


def download(key: str, private_key: bytes) -> Dict:
    """Download a key, decrypt it, and output it as a binary string.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> from test.hmt_escrow.utils import manifest
    >>> from hmt_escrow.job import Job
    >>> pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials=credentials, escrow_manifest=manifest)
    >>> (hash_, manifest_url) = upload(job.serialized_manifest, pub_key)
    >>> manifest_dict = download(manifest_url, job.gas_payer_priv)
    >>> manifest_dict == job.serialized_manifest
    True

    >>> job = Job(credentials=credentials, escrow_manifest=manifest)
    >>> (hash_, manifest_url) = upload(job.serialized_manifest, pub_key)
    >>> manifest_dict = download(manifest_url, job.gas_payer_priv)
    >>> manifest_dict == job.serialized_manifest
    True

    Args:
        key (str): This is the hash code returned when uploading.
        private_key (str): The private_key to decrypt this string with.

    Returns:
        Dict: returns the contents of the filename which was previously uploaded.

    Raises:
        Exception: if reading from fails.

    """
    try:
        content = download_from_storage(key)

        if crypto.is_encrypted(content) is True:
            content = crypto.decrypt(private_key, content)

    except Exception as e:
        LOG.warning(
            "Reading the key {!r} with private key {!r} with S3 failed because of: {!r}".format(
                key, private_key, e
            )
        )
        raise e
    return json.loads(content)


def upload(msg: Dict,
           public_key: bytes,
           encrypt_data: Optional[bool] = False) -> Tuple[str, str]:
    """Upload and encrypt a string for later retrieval.
    This can be manifest files, results, or anything that's been already
    encrypted.

    >>> from test.hmt_escrow.utils import manifest
    >>> from hmt_escrow.job import Job
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

    >>> job = Job(credentials=credentials, escrow_manifest=manifest)
    >>> (hash_, manifest_url) = upload(job.serialized_manifest, pub_key)
    >>> manifest_url.startswith('s3')
    True
    >>> manifest_dict = download(manifest_url, job.gas_payer_priv)
    >>> manifest_dict == job.serialized_manifest
    True

    Args:
        msg (Dict): The message to upload and encrypt.
        public_key (bytes): The public_key to encrypt the file for.
        encrypt_data (bool): Whether data must be encrypted before uploading.

    Returns:
        Tuple[str, str]: returns the contents of the filename which was previously uploaded.

    Raises:
        Exception: if adding bytes fails.

    """
    try:
        content = json.dumps(msg, sort_keys=True)
    except Exception as e:
        LOG.error("Can't extract the json from the dict")
        raise e

    hash_ = hashlib.sha1(content.encode("utf-8")).hexdigest()
    key = f"s3{hash_}"

    if encrypt_data:
        content = crypto.encrypt(public_key, content)

    BOTO3_CLIENT = _connect_s3()
    BOTO3_CLIENT.put_object(Bucket=ESCROW_BUCKETNAME,
                            Key=key,
                            Body=content)

    LOG.debug(f"Uploaded to S3, key: {key}")
    return hash_, key
