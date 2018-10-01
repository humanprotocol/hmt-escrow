import codecs
import hashlib
import json
from typing import Any, Tuple

import ipfsapi
import os

from devp2p import crypto

API = None
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
    msg = _decrypt(private_key, ciphertext).decode('unicode_escape')
    return json.loads(msg)


def upload(msg: dict, public_key: bytes,
           private_key: bytes) -> Tuple[Any, Any]:
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
    key = API.add_bytes(_encrypt(private_key, public_key, manifest_))
    return hash_, key


def _decrypt(private_key: bytes, msg: str):
    priv_key = codecs.decode(private_key, 'hex')
    e = crypto.ECCx(raw_privkey=priv_key)
    return e.decrypt(msg)


def _encrypt(private_key: bytes, public_key: bytes, msg: str):
    e = crypto.ECCx(raw_privkey=codecs.decode(private_key, 'hex'))
    return e.encrypt(msg, codecs.decode(public_key, 'hex'))
