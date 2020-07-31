import logging
import os
import time
import unittest

from solcx import compile_files
from web3 import Web3
from web3.providers import HTTPProvider
from web3.providers.eth_tester import EthereumTesterProvider
from web3.types import TxReceipt
from eth_typing import Address, ChecksumAddress, HexAddress, HexStr
from web3.contract import Contract
from web3.middleware import geth_poa_middleware
from web3._utils.transactions import wait_for_transaction_receipt
from hmt_escrow.kvstore_abi import abi as kvstore_abi
from typing import Dict, List, Tuple, Optional, Any

AttributeDict = Dict[str, Any]

GAS_LIMIT = int(os.getenv("GAS_LIMIT", 4712388))

LOG = logging.getLogger("hmt_escrow.eth_bridge")
HMTOKEN_ADDR = Web3.toChecksumAddress(
    os.getenv("HMTOKEN_ADDR", "0x9b0ff099c4e8df24ec077e0ccd46571f915afb25")
)

CONTRACT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "contracts")
CONTRACTS = compile_files(
    [
        "{}/Escrow.sol".format(CONTRACT_FOLDER),
        "{}/EscrowFactory.sol".format(CONTRACT_FOLDER),
        "{}/HMToken.sol".format(CONTRACT_FOLDER),
        "{}/HMTokenInterface.sol".format(CONTRACT_FOLDER),
        "{}/SafeMath.sol".format(CONTRACT_FOLDER),
    ]
)

# See more details about the eth-kvstore here: https://github.com/hCaptcha/eth-kvstore
KVSTORE_CONTRACT = Web3.toChecksumAddress(
    os.getenv("KVSTORE_CONTRACT", "0xbcF8274FAb0cbeD0099B2cAFe862035a6217Bf44")
)
WEB3_POLL_LATENCY = float(os.getenv("WEB3_POLL_LATENCY", 5))
WEB3_TIMEOUT = int(os.getenv("WEB3_TIMEOUT", 240))


def get_w3() -> Web3:
    """Set up the web3 provider for serving transactions to the ethereum network.

    >>> w3 = get_w3()
    >>> type(w3)
    <class 'web3.main.Web3'>

    Returns:
        Web3: returns the web3 provider.

    """
    endpoint = os.getenv("HMT_ETH_SERVER", "http://localhost:8545")
    if not endpoint:
        LOG.error("Using EthereumTesterProvider as we have no HMT_ETH_SERVER")
    provider = HTTPProvider(endpoint) if endpoint else EthereumTesterProvider()
    w3 = Web3(provider)
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


def handle_transaction(txn_func, *args, **kwargs) -> TxReceipt:
    """Handles a transaction that updates the contract state by locally
    signing, building, sending the transaction and returning a transaction
    receipt.

    Args:
        txn_func: the transaction function to be handled.

        \*args: all the arguments the function takes.

        \*\*kwargs: the transaction data used to complete the transaction.

    Returns:
        AttributeDict: returns the transaction receipt.

    Raises:
        TimeoutError: if waiting for the transaction receipt times out.
    """
    gas_payer = kwargs["gas_payer"]
    gas_payer_priv = kwargs["gas_payer_priv"]
    gas = kwargs["gas"]

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(gas_payer)

    txn_dict = txn_func(*args).buildTransaction(
        {"from": gas_payer, "gas": gas, "nonce": nonce}
    )

    signed_txn = w3.eth.account.signTransaction(txn_dict, private_key=gas_payer_priv)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

    try:
        txn_receipt = wait_for_transaction_receipt(
            w3, txn_hash, timeout=WEB3_TIMEOUT, poll_latency=WEB3_POLL_LATENCY
        )
    except TimeoutError as e:
        raise e
    return txn_receipt


def get_contract_interface(contract_entrypoint):
    """Retrieve the contract interface of a given contract.

    Args:
        contract_entrypoint: the entrypoint of the compiled source.

    Returns:
        returns the contract interface containing the contract abi.

    """
    compiled_sol = CONTRACTS
    contract_interface = compiled_sol[contract_entrypoint]
    return contract_interface


def get_hmtoken(hmtoken_addr=HMTOKEN_ADDR) -> Contract:
    """Retrieve the HMToken contract from a given address.

    >>> type(get_hmtoken())
    <class 'web3._utils.datatypes.Contract'>

    Returns:
        Contract: returns the HMToken solidity contract.

    """
    w3 = get_w3()
    contract_interface = get_contract_interface(
        "{}/HMTokenInterface.sol:HMTokenInterface".format(CONTRACT_FOLDER)
    )
    contract = w3.eth.contract(address=hmtoken_addr, abi=contract_interface["abi"])
    return contract


def get_escrow(escrow_addr: str) -> Contract:
    """Retrieve the Escrow contract from a given address.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials=credentials, escrow_manifest=manifest)

    Deploying a new Job to the ethereum network succeeds.
    
    >>> job.launch(rep_oracle_pub_key)
    True
    >>> type(get_escrow(job.job_contract.address))
    <class 'web3._utils.datatypes.Contract'>

    Args:
        escrow_addr (str): an ethereum address of the escrow contract.

    Returns:
        Contract: returns the Escrow solidity contract.

    """

    w3 = get_w3()
    contract_interface = get_contract_interface(
        "{}/Escrow.sol:Escrow".format(CONTRACT_FOLDER)
    )
    escrow = w3.eth.contract(
        address=ChecksumAddress(HexAddress(HexStr(escrow_addr))),
        abi=contract_interface["abi"],
    )
    return escrow


def get_factory(factory_addr: str) -> Contract:
    """Retrieve the EscrowFactory contract from a given address.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> job = Job(credentials=credentials, escrow_manifest=manifest)
    >>> type(get_factory(job.factory_contract.address))
    <class 'web3._utils.datatypes.Contract'>

    Args:
        factory_addr (str): the ethereum address of the Escrow contract.

    Returns:
        Contract: returns the EscrowFactory solidity contract.

    """
    w3 = get_w3()
    contract_interface = get_contract_interface(
        "{}/EscrowFactory.sol:EscrowFactory".format(CONTRACT_FOLDER)
    )
    escrow_factory = w3.eth.contract(
        address=ChecksumAddress(HexAddress(HexStr(factory_addr))),
        abi=contract_interface["abi"],
    )
    return escrow_factory


def deploy_factory(gas: int = GAS_LIMIT, **credentials) -> str:
    """Deploy an EscrowFactory solidity contract to the ethereum network.

    Args:
        gas (int): maximum amount of gas the caller is ready to pay.

    Returns
        str: returns the contract address of the newly deployed factory.

    """
    gas_payer = credentials["gas_payer"]
    gas_payer_priv = credentials["gas_payer_priv"]

    w3 = get_w3()
    contract_interface = get_contract_interface(
        "{}/EscrowFactory.sol:EscrowFactory".format(CONTRACT_FOLDER)
    )
    factory = w3.eth.contract(
        abi=contract_interface["abi"], bytecode=contract_interface["bin"]
    )

    txn_func = factory.constructor
    func_args = [HMTOKEN_ADDR]
    txn_info = {"gas_payer": gas_payer, "gas_payer_priv": gas_payer_priv, "gas": gas}
    txn_receipt = handle_transaction(txn_func, *func_args, **txn_info)
    contract_addr = txn_receipt["contractAddress"]
    return str(contract_addr)


def get_pub_key_from_addr(wallet_addr: str) -> bytes:
    """
    Given a wallet address, uses the kvstore to pull down the public key for a user
    in the hmt universe, defined by the kvstore key `hmt_pub_key`.  Works with the
    `set_pub_key_at_address` function.

    Requires that the `GAS_PAYER` environment variable be set to the
    address that will be paying for the transaction on the ethereum network

    Args:
        wallet_addr (string): address to get the public key of

    Returns:
        bytes: the public key in bytes form

    >>> import os
    >>> from web3 import Web3
    >>> get_pub_key_from_addr('badaddress')
    Traceback (most recent call last):
      File "/usr/lib/python3.6/doctest.py", line 1330, in __run
        compileflags, 1), test.globs)
      File "<doctest __main__.get_pub_key_from_addr[2]>", line 1, in <module>
        get_pub_key_from_addr('blah')
      File "hmt_escrow/eth_bridge.py", line 268, in get_pub_key_from_addr
        raise ValueError('environment variable GAS_PAYER required')
    ValueError: environment variable GAS_PAYER required
    >>> os.environ['GAS_PAYER'] = "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92"
    >>> os.environ['GAS_PAYER_PRIV'] = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    >>> pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> set_pub_key_at_addr(pub_key)  #doctest: +ELLIPSIS
    AttributeDict({'transactionHash': ...})
    >>> get_pub_key_from_addr(os.environ['GAS_PAYER'])
    b'2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d'

    """
    # TODO: Should we try to get the checksum address here instead of assuming user will do that?
    GAS_PAYER = os.getenv("GAS_PAYER")

    if not GAS_PAYER:
        raise ValueError("environment variable GAS_PAYER required")

    w3 = get_w3()

    kvstore = w3.eth.contract(address=KVSTORE_CONTRACT, abi=kvstore_abi)
    addr_pub_key = kvstore.functions.get(GAS_PAYER, "hmt_pub_key").call(
        {"from": GAS_PAYER}
    )

    return bytes(addr_pub_key, encoding="utf-8")


def set_pub_key_at_addr(pub_key: str) -> TxReceipt:
    """
    Given a public key, this function will use the eth-kvstore to reach out to the blockchain
    and set the key `hmt_pub_key` on the callers kvstore collection of values, equivalent to the
    argument passed in here.  This will be used by HMT to encrypt data for the receiver

    See more about kvstore here: https://github.com/hCaptcha/eth-kvstore

    Args:
        pub_key (string): RSA Public key for this user

    Returns:
        AttributeDict: receipt of the set transaction on the blockchain


    >>> from web3 import Web3
    >>> import os
    >>> os.environ['GAS_PAYER'] = "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92"
    >>> os.environ['GAS_PAYER_PRIV'] = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    >>> pub_key_to_set = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> set_pub_key_at_addr(pub_key_to_set)  #doctest: +ELLIPSIS
    AttributeDict({'transactionHash': ...})

    """
    GAS_PAYER = os.getenv("GAS_PAYER")
    GAS_PAYER_PRIV = os.getenv("GAS_PAYER_PRIV")

    if not (GAS_PAYER or GAS_PAYER_PRIV):
        raise ValueError("environment variable GAS_PAYER AND GAS_PAYER_PRIV required")

    w3 = get_w3()
    kvstore = w3.eth.contract(address=KVSTORE_CONTRACT, abi=kvstore_abi)

    txn_func = kvstore.functions.set
    func_args = ["hmt_pub_key", pub_key]
    txn_info = {
        "gas_payer": GAS_PAYER,
        "gas_payer_priv": GAS_PAYER_PRIV,
        "gas": GAS_LIMIT,
    }

    return handle_transaction(txn_func, *func_args, **txn_info)


class EthBridgeTestCase(unittest.TestCase):
    def setUp(self):
        from job import Job

        self.credentials = {
            "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
            "gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        }
        self.rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        self.job = Job(credentials=self.credentials, escrow_manifest=manifest)

    def test_handle_transaction(self):
        from web3.datastructures import AttributeDict as Web3AttributeDict

        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        gas = 4712388
        hmt_amount = int(self.job.amount * 10 ** 18)
        hmtoken_contract = get_hmtoken()
        txn_func = hmtoken_contract.functions.transfer
        func_args = [self.job.job_contract.address, hmt_amount]
        txn_info = {
            "gas_payer": self.job.gas_payer,
            "gas_payer_priv": self.job.gas_payer_priv,
            "gas": gas,
        }
        txn_receipt = handle_transaction(txn_func, *func_args, **txn_info)
        self.assertIs(type(txn_receipt), Web3AttributeDict)

    def test_get_escrow(self):
        self.job.launch(self.rep_oracle_pub_key)
        self.assertIsNotNone(get_escrow(self.job.job_contract.address))

    def test_get_factory(self):
        self.assertIsNotNone(get_factory(self.job.factory_contract.address))

    def test_get_pub_key_from_address(self):
        with self.assertRaises(ValueError):
            get_pub_key_from_addr("badaddress")
        os.environ["GAS_PAYER"] = self.credentials["gas_payer"]
        os.environ["GAS_PAYER_PRIV"] = self.credentials["gas_payer_priv"]
        set_pub_key_at_addr(self.rep_oracle_pub_key)
        self.assertEqual(
            get_pub_key_from_addr(os.environ["GAS_PAYER"]), self.rep_oracle_pub_key
        )

    def test_set_pub_key_at_address(self):
        os.environ["GAS_PAYER"] = self.credentials["gas_payer"]
        os.environ["GAS_PAYER_PRIV"] = self.credentials["gas_payer_priv"]
        self.assertIsNotNone(
            set_pub_key_at_addr(self.rep_oracle_pub_key).transactionHash
        )


if __name__ == "__main__":
    from test_manifest import manifest

    unittest.main(exit=False)
