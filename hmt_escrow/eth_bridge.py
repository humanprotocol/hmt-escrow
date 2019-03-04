import logging
import os
import time

from solc import compile_files
from web3 import Web3, HTTPProvider, EthereumTesterProvider
from web3.contract import Contract
from web3.middleware import geth_poa_middleware
from typing import Dict, Tuple, Optional, Any

AttributeDict = Dict[str, Any]

DEFAULT_GAS = int(os.getenv("DEFAULT_GAS", 4712388))

LOG = logging.getLogger("hmt_escrow.eth_bridge")
HMTOKEN_ADDR = Web3.toChecksumAddress(
    os.getenv("HMTOKEN_ADDR", '0x9b0ff099c4e8df24ec077e0ccd46571f915afb25'))

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
    """Set up the web3 provider for serving transactions to the ethereum network.

    >>> w3 = get_w3()
    >>> type(w3)
    <class 'web3.main.Web3'>
    
    Returns:
        Web3: returns the web3 provider.

    """
    endpoint = os.getenv("HMT_ETH_SERVER", 'http://localhost:8545')
    if not endpoint:
        LOG.error("Using EthereumTesterProvider as we have no HMT_ETH_SERVER")
    provider = HTTPProvider(endpoint) if endpoint else EthereumTesterProvider
    w3 = Web3(provider)
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)
    return w3


def handle_transaction(txn_dict: Dict[str, Any],
                       priv_key: Optional[str] = None) -> AttributeDict:
    w3 = get_w3()
    signed_txn = w3.eth.account.signTransaction(txn_dict, private_key=priv_key)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

    try:
        txn_receipt = w3.eth.waitForTransactionReceipt(txn_hash, timeout=240)
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


def get_hmtoken() -> Contract:
    """Retrieve the HMToken contract from a given address.

    Returns:
        Contract: returns the HMToken solidity contract.

    """
    w3 = get_w3()
    contract_interface = get_contract_interface(
        '{}/HMTokenInterface.sol:HMTokenInterface'.format(CONTRACT_FOLDER))
    contract = w3.eth.contract(
        address=HMTOKEN_ADDR, abi=contract_interface['abi'])
    return contract


def get_escrow(escrow_address: str) -> Contract:
    """Retrieve the Escrow contract from a given address.

    Args:
        escrow_address (str): the ethereum address of the Escrow contract.

    Returns:
        Contract: returns the Escrow solidity contract.
        
    """

    w3 = get_w3()
    contract_interface = get_contract_interface(
        '{}/Escrow.sol:Escrow'.format(CONTRACT_FOLDER))
    escrow = w3.eth.contract(
        address=escrow_address, abi=contract_interface['abi'])
    return escrow


def get_factory(factory_address: str) -> Contract:
    """Retrieve the EscrowFactory contract from a given address.

    Args:
        factory_address (str): the ethereum address of the Escrow contract.

    Returns:
        Contract: returns the EscrowFactory solidity contract.
        
    """
    w3 = get_w3()
    contract_interface = get_contract_interface(
        '{}/EscrowFactory.sol:EscrowFactory'.format(CONTRACT_FOLDER))
    escrow_factory = w3.eth.contract(
        address=factory_address, abi=contract_interface['abi'])
    return escrow_factory


def deploy_contract(contract_interface,
                    gas_payer: str,
                    gas_payer_priv: str,
                    gas: int = DEFAULT_GAS,
                    args=[]) -> Tuple[Contract, str]:
    """Deploy a given contract to the ethereum network.

    Args:
        contract_interface: the interface of a contract containing the abi and the binary.
        gas (int): maximum amount of gas the caller is ready to pay.
        args: additional arguments like the HMToken address.

    Returns:
        Tuple[Contract, str]: returns a tuple of the solidity contract and its ethereum address.
        
    """
    w3 = get_w3()
    contract = w3.eth.contract(
        abi=contract_interface['abi'], bytecode=contract_interface['bin'])
    nonce = w3.eth.getTransactionCount(gas_payer)

    # Get transaction hash from deployed contract
    LOG.debug("Deploying contract with gas:{}".format(gas))

    txn_dict = contract.constructor(*args).buildTransaction({
        'from': gas_payer,
        'gas': gas,
        'nonce': nonce
    })
    txn_receipt = handle_transaction(txn_dict, gas_payer_priv)
    contract_address = txn_receipt['contractAddress']

    contract = w3.eth.contract(
        address=contract_address,
        abi=contract_interface['abi'],
    )

    LOG.info("New contract at:{} ".format(contract_address))
    return contract, contract_address


def deploy_factory(gas_payer: str, gas_payer_priv: str,
                   gas: int = DEFAULT_GAS) -> str:
    """Deploy an EscrowFactory solidity contract to the ethereum network.

    Args:
        gas (int): maximum amount of gas the caller is ready to pay.

    Returns
        str: returns the contract address of the newly deployed factory.

    """

    contract_interface = get_contract_interface(
        '{}/EscrowFactory.sol:EscrowFactory'.format(CONTRACT_FOLDER))
    (contract, contract_address) = deploy_contract(
        contract_interface,
        gas_payer,
        gas_payer_priv,
        gas,
        args=[HMTOKEN_ADDR])
    return contract_address


if __name__ == "__main__":
    import doctest
    doctest.testmod()
