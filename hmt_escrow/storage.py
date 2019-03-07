import logging
import codecs
import hashlib
import json
from typing import Dict, Tuple

import ipfsapi
import os

from eth_keys import keys
from p2p import ecies

SHARED_MAC_DATA = os.getenv(
    "SHARED_MAC",
    b'9da0d3721774843193737244a0f3355191f66ff7321e83eae83f7f746eb34350')

LOG = logging.getLogger("hmt_escrow.storage")

if not os.getenv("IPFS_DISABLE"):
    _host = os.getenv("IPFS_HOSTNAME", 'localhost')
    _port = int(os.getenv("IPFS_TCP_PORT", '5001'))
    try:
        API = ipfsapi.connect(_host, _port)
    except Exception as e:
        raise e
        LOG.error("Connection with IPFS failed because of: {}".format(e))


def download(key: str, private_key: bytes) -> Dict:
    """Download a key, decrypt it, and output it as a binary string.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials, manifest)
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
        Exception: if reading from IPFS fails.

    """
    try:
        ciphertext = API.cat(key)
    except Exception as e:
        LOG.warning("Reading the key with IPFS failed because of: {}".format(e))
        raise e
    msg = _decrypt(private_key, ciphertext)
    return json.loads(msg)


def upload(msg: Dict, public_key: bytes) -> Tuple[str, str]:
    """Upload and encrypt a string for later retrieval.
    This can be manifest files, results, or anything that's been already
    encrypted.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials, manifest)
    >>> (hash_, manifest_url) = upload(job.serialized_manifest, pub_key)
    >>> manifest_dict = download(manifest_url, job.gas_payer_priv)
    >>> manifest_dict == job.serialized_manifest
    True

    Args:
        msg (Dict): The message to upload and encrypt.
        public_key (bytes): The public_key to encrypt the file for.

    Returns:
        Tuple[str, str]: returns the contents of the filename which was previously uploaded.
    
    Raises:
        Exception: if adding bytes with IPFS fails.

    """
    manifest_ = json.dumps(msg, sort_keys=True)
    hash_ = hashlib.sha1(manifest_.encode('utf-8')).hexdigest()
    try:
        key = API.add_bytes(_encrypt(public_key, manifest_))
    except Exception as e:
        LOG.warning("Adding bytes with IPFS failed because of: {}".format(e))
        raise e
    return hash_, key


def _decrypt(private_key: bytes, msg: bytes) -> str:
    """Use ECIES to decrypt a message with a given private key and an optional MAC.

    >>> priv_key = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    >>> pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> msg = "test"
    >>> _decrypt(priv_key, _encrypt(pub_key, msg)) == msg
    True
    
    Using a wrong public key to decrypt a message results in failure.
    >>> false_pub_key = b"74c81fe41b30f741b31185052664a10c3256e2f08bcfb20c8f54e733bef58972adcf84e4f5d70a979681fd39d7f7847d2c0d3b5d4aead806c4fec4d8534be114"
    >>> _decrypt(priv_key, _encrypt(false_pub_key, msg)) == msg
    Traceback (most recent call last):
    p2p.exceptions.DecryptionError: Failed to verify tag

    Args:
        private_key (bytes): The private_key to decrypt the message with.
        msg (bytes): The message to be decrypted.
    
    Returns:
        str: returns the plaintext equivalent to the originally encrypted one.

    """
    priv_key = keys.PrivateKey(codecs.decode(private_key, 'hex'))
    e = ecies.decrypt(msg, priv_key, shared_mac_data=SHARED_MAC_DATA)
    return e.decode(encoding='utf-8')


def _encrypt(public_key: bytes, msg: str) -> bytes:
    """Use ECIES to encrypt a message with a given public key and optional MAC.

    >>> priv_key = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    >>> pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> msg = "test"
    >>> _decrypt(priv_key, _encrypt(pub_key, msg)) == msg
    True

    Args:
        public_key (bytes): The public_key to encrypt the message with.
        msg (str): The message to be encrypted.
    
    Returns:
        bytes: returns the cryptotext encrypted with the public key.

    """
    pub_key = keys.PublicKey(codecs.decode(public_key, 'hex'))
    msg_bytes = msg.encode(encoding='utf-8')
    return ecies.encrypt(msg_bytes, pub_key, shared_mac_data=SHARED_MAC_DATA)


if __name__ == "__main__":
    import doctest
    from job import Job
    from test_manifest import manifest
    doctest.testmod()
