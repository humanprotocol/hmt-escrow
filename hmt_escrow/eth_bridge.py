import logging
import os
import time

from solc import compile_files
from web3 import Web3, HTTPProvider, EthereumTesterProvider
from web3.contract import Contract
from web3.middleware import geth_poa_middleware
from typing import Dict, Tuple, Union

AttributeDict = Dict[str, Union[int, str]]

DEFAULT_GAS = int(os.getenv("DEFAULT_GAS", 4712388))
GAS_PAYER = Web3.toChecksumAddress(
    os.getenv("GAS_PAYER", "0x1413862c2b7054cdbfdc181b83962cb0fc11fd92"))
GAS_PAYER_PRIV = os.getenv(
    "GAS_PAYER_PRIV",
    "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5")

LOG = logging.getLogger("api.eth_bridge")
EIP20ADDR = Web3.toChecksumAddress(
    os.getenv("EIP20ADDR", '0x9b0ff099c4e8df24ec077e0ccd46571f915afb25'))

CONTRACT_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'contracts')
CONTRACTS = compile_files([
    "{}/Escrow.sol".format(CONTRACT_FOLDER),
    "{}/EscrowFactory.sol".format(CONTRACT_FOLDER),
    "{}/HMToken.sol".format(CONTRACT_FOLDER),
    "{}/HMTokenInterface.sol".format(CONTRACT_FOLDER),
    "{}/SafeMath.sol".format(CONTRACT_FOLDER)
])


def get_w3() -> Web3:
    endpoint = os.getenv("HMT_ETH_SERVER", 'http://localhost:8545')
    if not endpoint:
        LOG.error("Using EthereumTesterProvider as we have no HMT_ETH_SERVER")
    provider = HTTPProvider(endpoint) if endpoint else EthereumTesterProvider
    w3 = Web3(provider)
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)
    return w3


def wait_on_transaction(tx_hash: str) -> AttributeDict:
    w3 = get_w3()
    LOG.debug("Waiting to get transaction recipt")
    return w3.eth.waitForTransactionReceipt(tx_hash, timeout=240)


def sign_and_send_transaction(tx_hash: str, private_key: str) -> str:
    w3 = get_w3()
    signed_txn = w3.eth.account.signTransaction(
        tx_hash, private_key=private_key)
    return w3.eth.sendRawTransaction(signed_txn.rawTransaction)


def get_contract_interface(contract_entrypoint):
    compiled_sol = CONTRACTS
    contract_interface = compiled_sol[contract_entrypoint]
    return contract_interface


def get_eip20() -> Contract:
    w3 = get_w3()
    contract_interface = get_contract_interface(
        '{}/HMTokenInterface.sol:HMTokenInterface'.format(CONTRACT_FOLDER))
    contract = w3.eth.contract(
        address=EIP20ADDR, abi=contract_interface['abi'])
    return contract


def get_escrow(escrow_address: str, gas: int = DEFAULT_GAS) -> Contract:
    contract_interface = get_contract_interface(
        '{}/Escrow.sol:Escrow'.format(CONTRACT_FOLDER))
    escrow = get_w3().eth.contract(
        address=escrow_address, abi=contract_interface['abi'])
    return escrow


def get_factory(factory_address: str, gas: int = DEFAULT_GAS) -> Contract:
    contract_interface = get_contract_interface(
        '{}/EscrowFactory.sol:EscrowFactory'.format(CONTRACT_FOLDER))
    escrow_factory = get_w3().eth.contract(
        address=factory_address, abi=contract_interface['abi'])
    return escrow_factory


def deploy_factory(gas: int = DEFAULT_GAS) -> Contract:
    """
    Returns success
    sol: solidity code
    gas: how much gas to use for the contract
    contract = input path into sol contract
    """

    contract_interface = get_contract_interface(
        '{}/EscrowFactory.sol:EscrowFactory'.format(CONTRACT_FOLDER))
    (contract, contract_address) = deploy_contract(
        contract_interface, gas, args=[EIP20ADDR])
    return contract
