import codecs
import hashlib
import json
from typing import Any, Tuple

import ipfsapi
import os

from eth_keys import keys
from p2p import ecies

API = None
SHARED_MAC_DATA = os.getenv(
    "SHARED_MAC",
    b'9da0d3721774843193737244a0f3355191f66ff7321e83eae83f7f746eb34350')

if not os.getenv("IPFS_DISABLE"):
    _host = os.getenv("IPFS_HOSTNAME", 'localhost')
    # Stupid name so not to fight with k8s
    _port = int(os.getenv("IPFS_TCP_PORT", '5001'))
    API = ipfsapi.connect(_host, _port)


def download(key: str, private_key: bytes) -> dict:
    """
    Download a key, decrypt it, and output it as a binary string
    :param private_key: The private_key to decrypt this string with.
    :param key: This is the hash code returned when uploading
    :return: The contents of the filename which was previously uploaded
    """
    ciphertext = API.cat(key)
    msg = _decrypt(private_key, ciphertext)
    return json.loads(msg)


def upload(msg: dict, public_key: bytes) -> Tuple[Any, Any]:
    """
    Upload and encrypt a string for later retrieval.
    This can be manifest files, results, or anything that's been already
    encrypted.
    :param msg: The message to upload and encrypt
    :param public_key: The public_key to encrypt the file for
    :param private_key: The private_key to encrypt the file with
    :return: The contents of the filename which was previously uploaded
    """
    manifest_ = json.dumps(msg, sort_keys=True, ensure_ascii=True)
    hash_ = hashlib.sha1(manifest_.encode('utf-8')).hexdigest()
    key = API.add_bytes(_encrypt(public_key, manifest_))
    return hash_, key


def _decrypt(private_key: bytes, msg: bytes):
    priv_key = keys.PrivateKey(codecs.decode(private_key, 'hex'))
    e = ecies.decrypt(msg, priv_key, shared_mac_data=SHARED_MAC_DATA)
    return e.decode(encoding='utf-8')


def _encrypt(public_key: bytes, msg: str):
    pub_key = keys.PublicKey(codecs.decode(public_key, 'hex'))
    msg_bytes = msg.encode(encoding='utf-8')
    return ecies.encrypt(msg_bytes, pub_key, shared_mac_data=SHARED_MAC_DATA)
