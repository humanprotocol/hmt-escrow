import codecs
import hashlib
import json
import logging
import os
import sys
from typing import Dict, Tuple

import ipfsapi
import timeout_decorator
from eth_keys import keys
from ipfsapi import Client
from p2p import ecies

SHARED_MAC_DATA = os.getenv(
    "SHARED_MAC",
    b'9da0d3721774843193737244a0f3355191f66ff7321e83eae83f7f746eb34350')

LOG = logging.getLogger("hmt_escrow.storage")
IPFS_HOST = os.getenv("IPFS_HOST", "localhost")
IPFS_PORT = int(os.getenv("IPFS_PORT", 5001))
IPNS_PATH = os.getenv("IPNS_PATH", f"{IPFS_HOST}:{IPFS_PORT}/ipns/")


@timeout_decorator.timeout(20)
def _connect(host: str, port: int) -> Client:
    try:
        IPFS_CLIENT = ipfsapi.connect(host, port)
        return IPFS_CLIENT
    except Exception as e:
        LOG.error("Connection with IPFS failed because of: {}".format(e))
        raise e


IPFS_CLIENT = _connect(IPFS_HOST, IPFS_PORT)


def download(key: str, private_key: bytes) -> Dict:
    """Download a ipfs key/hash-location, decrypt it, and output it as a binary string.

    Args:
        key (str): This is the hash code returned when uploading.
        private_key (str): The private_key to decrypt this string with.

    Returns:
        Dict: returns the contents of the filename which was previously uploaded.
    
    Raises:
        Exception: if reading from IPFS fails.

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
    """

    # Q prefix is ipfs. If no q prefix, assume IPNS: https://github.com/ipfs/faq/issues/22
    is_ipns = lambda s: s[0] != 'Q'

    if is_ipns(key):
        res = IPFS_CLIENT.resolve(f'{IPNS_PATH}{key}')
        ipfs_path = res['Path']
        key = ipfs_path.split('/')[-1]
    try:
        LOG.debug("Downloading key: {}".format(key))
        ciphertext = IPFS_CLIENT.cat(key)
    except Exception as e:
        LOG.warning(
            f'Reading the key {str(key)} with private key {str(private_key)} with IPFS failed because of: {str(e)}'
        )
        raise e
    msg = _decrypt(private_key, ciphertext)
    return json.loads(msg)


@timeout_decorator.timeout(20)
def upload(msg: Dict, public_key: bytes,
           ipns_keypair_name: str = '') -> Tuple[str, str]:
    """Upload encrypted string to IPFS.
    This can be manifest files, results, or anything that's been already encrypted.
    Optionally pins the file to IPNS. Pass in the IPNS key name 
    To get IPNS key name, see create_new_ipns_link

    Args:
        msg (Dict): The message to upload and encrypt.
        public_key (bytes): The public_key to encrypt the file for.
        ipns_keypair_name (str): If left blank, then don't pin to IPNS

    Returns:
        Tuple[str, str]: returns [sha1 hash, ipfs hash]
    
    Raises:
        Exception: if adding bytes with IPFS fails.

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
    """

    try:
        manifest_ = json.dumps(msg, sort_keys=True)
    except Exception as e:
        LOG.error("Can't extract the json from the dict")
        raise e

    hash_ = hashlib.sha1(manifest_.encode('utf-8')).hexdigest()
    try:
        ipfs_file_hash = IPFS_CLIENT.add_bytes(_encrypt(public_key, manifest_))
    except Exception as e:
        LOG.warning("Adding bytes with IPFS failed because of: {}".format(e))
        raise e

    if ipns_keypair_name != '':
        try:
            # publish ipns ... docs: https://ipfs.io/ipns/12D3KooWEqnTdgqHnkkwarSrJjeMP2ZJiADWLYADaNvUb6SQNyPF/docs/http_client_ref.html#ipfshttpclient.Client.name
            IPFS_CLIENT.name.publish(
                f'/ipfs/{ipfs_file_hash}',
                key=ipns_keypair_name.lower(),
                allow_offline=True)
        except Exception as e:
            LOG.warning("IPNS failed because of: {}".format(e))
            raise e

    return hash_, ipfs_file_hash


def create_new_ipns_link(name: str) -> str:
    """Create new ipns link, return the ID.
       The IPNS links are managed by key value system.

    Args:
        name (str): Name to call the ipns link. Retrieve the link w/ same name

    Returns:
        str: Returns the IPNS ID

    >>> import random 
    >>> key_name = str(random.getrandbits(32 * 8)) # get random, or else throws duplicate key error
    >>> create_new_ipns_link(key_name) != ''
    True
    """
    name = name.lower()
    IPFS_CLIENT.key.gen(name, 'ed25519')
    return get_ipns_link(name).split('/')[-1]


def ipns_link_exists(name: str) -> bool:
    """See if an IPNS link exists

    Args:
        name (str): Name we call ipns link

    Returns:
        bool: Returns True if link exists

    >>> import random 
    >>> key_name = str(random.getrandbits(32 * 8)) # get random, or else throws duplicate key error
    >>> _ = create_new_ipns_link(key_name)
    >>> ipns_link_exists(key_name)
    True
    >>> key_name = str(random.getrandbits(32 * 8))
    >>> ipns_link_exists(key_name)
    False
    """
    try:
        get_ipns_link(name)
        return True
    except Exception as e:
        return False
    return False


def get_ipns_link(name: str) -> str:
    """Get the ipns link with the name of it which we remember it by

    Args:
        name (str): Name we call ipns link

    Returns:
        str: Returns the IPNS url

    Raises:
        ValueError: if link not found

    >>> import random 
    >>> key_name = str(random.getrandbits(32 * 8)) # get random, or else throws duplicate key error
    >>> create_new_ipns_link(key_name) != ''
    True
    """
    keys = IPFS_CLIENT.key.list()
    does_match = lambda x: x['Name'] == name.lower()
    matches = list(filter(does_match, keys['Keys']))
    if len(matches) == 0:
        raise ValueError(f'IPNS link not found with name: "{name}"!')
    ipns_id = matches[0]['Id']  # get first match
    return f'{IPNS_PATH}{ipns_id}'


def _decrypt(private_key: bytes, msg: bytes) -> str:
    """Use ECIES to decrypt a message with a given private key and an optional MAC.

    Args:
        private_key (bytes): The private_key to decrypt the message with.
        msg (bytes): The message to be decrypted.
    
    Returns:
        str: returns the plaintext equivalent to the originally encrypted one.

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
    """
    priv_key = keys.PrivateKey(codecs.decode(private_key, 'hex'))
    e = ecies.decrypt(msg, priv_key, shared_mac_data=SHARED_MAC_DATA)
    return e.decode(encoding='utf-8')


def _encrypt(public_key: bytes, msg: str) -> bytes:
    """Use ECIES to encrypt a message with a given public key and optional MAC.

    Args:
        public_key (bytes): The public_key to encrypt the message with.
        msg (str): The message to be encrypted.
    
    Returns:
        bytes: returns the cryptotext encrypted with the public key.

    >>> priv_key = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    >>> pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> msg = "test"
    >>> _decrypt(priv_key, _encrypt(pub_key, msg)) == msg
    True
    """
    pub_key = keys.PublicKey(codecs.decode(public_key, 'hex'))
    msg_bytes = msg.encode(encoding='utf-8')
    return ecies.encrypt(msg_bytes, pub_key, shared_mac_data=SHARED_MAC_DATA)


if __name__ == "__main__":
    import doctest
    from test_manifest import manifest
    from job import Job
    doctest.testmod()
