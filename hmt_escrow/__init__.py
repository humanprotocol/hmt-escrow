import json
import logging
import os
import sys

from decimal import *
from web3 import Web3
from web3.contract import Contract
from enum import Enum
from typing import Dict, List, Tuple

# Access basemodels
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hmt_escrow.eth_bridge import get_hmtoken, get_contract_interface, wait_on_transaction, get_escrow, get_factory, deploy_factory, get_w3, sign_and_send_transaction
from hmt_escrow.storage import download, upload
from basemodels import Manifest

DEFAULT_GAS = int(os.getenv("DEFAULT_GAS", 4712388))
GAS_PAYER = Web3.toChecksumAddress(
    os.getenv("GAS_PAYER", "0x1413862c2b7054cdbfdc181b83962cb0fc11fd92"))
GAS_PAYER_PRIV = os.getenv(
    "GAS_PAYER_PRIV",
    "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5")
REP_ORACLE = Web3.toChecksumAddress(
    os.getenv("REP_ORACLE", "0x1413862c2b7054cdbfdc181b83962cb0fc11fd92"))
REC_ORACLE = Web3.toChecksumAddress(
    os.getenv("REC_ORACLE", "0x1413862c2b7054cdbfdc181b83962cb0fc11fd92"))
FACTORY_ADDR = os.getenv("FACTORY_ADDR", None)
LOG = logging.getLogger("hmt_escrow")


def _status(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> int:
    """Wrapper function that calls Escrow solidity contract's getStatus method in a read-only manner.

    Description of status codes:
    0: Launched
    1: Pending
    2: Partial
    3: Paid
    4: Complete
    5: Cancelled

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        int: returns the number equivalent to the status of the contract.

    """
    return escrow_contract.functions.getStatus().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _manifest_hash(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls Escrow solidity contract's getManifestHash method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the manifest hash

    """
    return escrow_contract.functions.getManifestHash().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _intermediate_results_hash(escrow_contract: Contract,
                               gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls Escrow solidity contract's getIntermediateResultsHash method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the intermediate results hash

    """
    return escrow_contract.functions.getIntermediateResultsHash().call({
        'from':
        GAS_PAYER,
        'gas':
        gas
    })


def _final_results_hash(escrow_contract: Contract,
                        gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls Escrow solidity contract's getFinalResultsHash method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the final results hash

    """
    return escrow_contract.functions.getFinalResultsHash().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _manifest_url(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls Escrow solidity contract's getManifestUrl method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the manifest url

    """
    return escrow_contract.functions.getManifestUrl().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _intermediate_results_url(escrow_contract: Contract,
                              gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls Escrow solidity contract's getIntermediateResultsUrl method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the intermediate results url

    """
    return escrow_contract.functions.getIntermediateResultsUrl().call({
        'from':
        GAS_PAYER,
        'gas':
        gas
    })


def _final_results_url(escrow_contract: Contract,
                       gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls Escrow solidity contract's getFinalResultsUrl method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the final results url

    """
    return escrow_contract.functions.getFinalResultsUrl().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _balance(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> int:
    """Wrapper function that calls Escrow solidity contract's getBalance method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        int: returns the balance of the contract.

    """
    return escrow_contract.functions.getBalance().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _bulk_payout(escrow_contract: Contract,
                 addresses: list,
                 amounts: list,
                 uri: str,
                 hash_: str,
                 gas: int = DEFAULT_GAS):
    """Wrapper function that calls Escrow solidity contract's bulkPayout method that creates a transaction to the network.

    Handles the conversion of the oracle_stake and fundable amount to contract's native values.
    amount: Multiply by 10^18 to get the correct amount in HMT dictated by solidity contract's decimals.

    Args:
        escrow_contract (Contract): the contract to be updated.
        addresses (list): ethereum addresses receiving payouts.
        amounts (list): corresponding list of HMT to be paid.
        uri (str): final manifest result url getting updated to the Escrow solidity contract's state.
        hash_ (str): final manifest result hash getting updated to the Escrow solidity contract's state.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if the payout was successful.
    
    Raises:
        TimeoutError: if wait_on_transaction times out.

    """

    hmt_amounts = [int(amount * 10**18) for amount in amounts]

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = escrow_contract.functions.bulkPayOut(addresses, hmt_amounts, uri,
                                                   hash_, 1).buildTransaction({
                                                       'from':
                                                       GAS_PAYER,
                                                       'gas':
                                                       gas,
                                                       'nonce':
                                                       nonce
                                                   })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)
    return True


def _store_results(escrow_contract: Contract,
                   uri: str,
                   hash_: str,
                   gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Escrow solidity contract's storeResults method that creates a transaction to the network.

    Args:
        escrow_contract (Contract): the contract to be updated.
        uri (str): intermediate manifest result url getting updated to the Escrow solidity contract's state.
        hash_ (str): intermediate manifest result hash getting updated to the Escrow solidity contract's state.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if intermediate results were successfully updated
    
    Raises:
        TimeoutError: if wait_on_transaction times out

    """
    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = escrow_contract.functions.storeResults(uri,
                                                     hash_).buildTransaction({
                                                         'from':
                                                         GAS_PAYER,
                                                         'gas':
                                                         gas,
                                                         'nonce':
                                                         nonce
                                                     })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)
    return True


def _complete(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Escrow solidity contract's complete method that creates a transaction to the network.

    Makes a separate call to check the status of the contract by using internal helper function _status.

    Args:
        escrow_contract (Contract): the contract to be updated.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Complete" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out

    """
    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = escrow_contract.functions.complete().buildTransaction({
        'from':
        GAS_PAYER,
        'gas':
        gas,
        'nonce':
        nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)
    return _status(escrow_contract) == 4


def _abort(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Escrow solidity contract's abort method that creates a transaction to the network.

    Makes a separate call to check the status of the contract by using internal helper function _status.

    Args:
        escrow_contract (Contract): the contract to be updated.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Cancelled" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out

    """
    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = escrow_contract.functions.abort().buildTransaction({
        'from': GAS_PAYER,
        'gas': gas,
        'nonce': nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)

    return _status(escrow_contract) == 5


def _refund(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Escrow solidity contract's refund method that creates a transaction to the network.

    Makes a separate call to check the status of the contract by using internal helper function _status.

    Args:
        escrow_contract (Contract): the contract to be updated.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Cancelled" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out

    """
    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = escrow_contract.functions.refund().buildTransaction({
        'from':
        GAS_PAYER,
        'gas':
        gas,
        'nonce':
        nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)

    return _status(escrow_contract) == 5


def _counter(factory_contract: Contract, gas: int = DEFAULT_GAS) -> int:
    """Wrapper function that calls EscrowFactory solidity contract's getCounter method in a read-only manner.

    Args:
        factory_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        int: returns the balance of the contract

    """
    return factory_contract.functions.getCounter().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _last_address(factory_contract: Contract, gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls EscrowFactory solidity contract's getLastAddress method in a read-only manner.

    Args:
        factory_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the last address of an escrow contract deployed by EscrowFactory

    """
    return factory_contract.functions.getLastAddress().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _create_escrow(factory_contract: Contract, gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls EscrowFactory solidity contract's createEscrow method that creates a transaction to the network.

    Args:
        factory_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if a new escrow (Pokémon) was successfully launched to the network.
    
    Raises:
        TimeoutError: if wait_on_transaction times out.

    """
    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)
    tx_dict = factory_contract.functions.createEscrow().buildTransaction({
        'from':
        GAS_PAYER,
        'gas':
        gas,
        'nonce':
        nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)
    return True


def _setup(escrow: 'Escrow', gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Escrow solidity contract's setup method that creates a transaction to the network.

    Handles the conversion of the oracle_stake and fundable amount to contract's native values:
    oracle_stake: Multiply by 100 to an integer value between 0 and 100.
    amount: Multiply by 10^18 to get the correct amount in HMT dictated by solidity contract's decimals.

    Args:
        escrow (Escrow): the Escrow class preferrably already initialized
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Pending" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out.

    """
    escrow_contract = escrow.job_contract
    reputation_oracle_stake = int(escrow.oracle_stake * 100)
    recording_oracle_stake = int(escrow.oracle_stake * 100)
    hmt_amount = int(escrow.amount * 10**18)

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = escrow_contract.functions.setup(
        escrow.reputation_oracle, escrow.recording_oracle,
        reputation_oracle_stake, recording_oracle_stake, hmt_amount,
        escrow.manifest_url, escrow.manifest_hash).buildTransaction({
            'from':
            GAS_PAYER,
            'gas':
            gas,
            'nonce':
            nonce
        })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)
    return _status(escrow_contract) == 1


def _transfer_to_address(address: str, amount: Decimal,
                         gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls HMToken solidity contract's transfer method that creates a transaction to the network.

    Handles the conversion of the oracle_stake and fundable amount to contract's native values:
    amount: Multiply by 10^18 to get the correct amount in HMT dictated by solidity contract's decimals.

    Args:
        address (str): an ethereum address to receive HMT.
        amount (Decimal): the amount of HMT to be paid before the decimal conversion.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Pending" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out.

    """
    hmtoken_contract = get_hmtoken()
    hmt_amount = int(amount * 10**18)

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = hmtoken_contract.functions.transfer(
        address, hmt_amount).buildTransaction({
            'from': GAS_PAYER,
            'gas': gas,
            'nonce': nonce
        })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)
    return True


class Escrow(Manifest):
    initialized = False

    def initialize(self, manifest: Dict) -> bool:
        """Initialize the class attributes for the Escrow class.

        Protects against re-entry.

        Args:
            manifest (Dict): a pre-serialized manifest containing data regarding a job.
        
        Returns:
            bool: returns True if all the class attributes have been set.
        
        Raises:
            Exception: if Escrow has been already initialized.

        """
        if self.initialized:
            raise Exception("Unable to reinitialize if we already have")
        self.per_job_cost = Decimal(manifest['task_bid_price'])
        self.oracle_stake = Decimal(manifest['oracle_stake'])
        self.recording_oracle = str(manifest['recording_oracle_addr'])
        self.reputation_oracle = str(manifest['reputation_oracle_addr'])
        self.number_of_answers = int(manifest['job_total_tasks'])
        self.oracle_stake = Decimal(manifest['oracle_stake'])
        self.amount = Decimal(self.per_job_cost * self.number_of_answers)
        self.initialized = True
        return True

    def deploy(self, public_key: bytes) -> bool:
        """Deploy a contract to the blockchain

        Launches a fresh new Escrow solidity contract (Pokémon) to the blockchain.
        Serializes a manifest and calls initialize to setup Escrow's class attributes.
        Uploads the the serialized manifest to IPFS with a public key of the Reputation Oracle.

        Args:
            public_key (bytes): public key of the Reputation Oracle

        Returns:
            bool: returns True if Class initialization and Ethereum and IPFS transactions succeed.

        """
        job_address = initialize_job()
        self.job_contract = get_escrow(job_address)
        serialized_manifest = self.serialize()
        self.initialize(serialized_manifest)
        (hash_, manifest_url) = upload(serialized_manifest, public_key)
        self.manifest_url = manifest_url
        self.manifest_hash = hash_
        return True

    def fund(self) -> bool:
        """Funds the Escrow solidity contract set in Escrow's class attributes.

        Returns:
            bool: returns True if contract is funded.

        """
        return _transfer_to_address(self.job_contract.address, self.amount)

    def abort(self) -> bool:
        """Transfers back the money to the funder of the Escrow solidity contract and destroys it.

        Returns:
            bool: returns True if contract initiator is refunded and contract gets destroyed successfully.

        """
        return _abort(self.job_contract)

    def refund(self) -> bool:
        """Transfers back the money to the funder of the Escrow solidity contract but doesn't destroy it.

        Softer version of abort as the Escrow solidity contract is not destroyed.
        Higher in gas costs however than abort.

        Returns:
            bool: returns True if refund to contract initiator succeeds.

        """
        return _refund(self.job_contract)

    def setup(self) -> bool:
        """Sets up the Escrow solidity contract with Escrow's class attributes.

        Returns:
            bool: returns True if job is pending.

        """
        return setup_job(self)

    def status(self) -> Enum:
        """Returns the status of a contract.

        Returns:
            Enum: returns the status as an enumeration.

        """
        return status(self.job_contract)

    def store_intermediate_results(self, results: Dict,
                                   public_key: bytes) -> bool:
        """Stores intermediate results with Reputation Oracle's public key to IPFS.

        Args:
            results (Dict): intermediate results of the Recording Oracle.
            public_key (bytes): public key of the Reputation Oracle.
        
        Returns:
            returns True if contract's state is updated and IPFS upload succeeds.

        """
        (hash_, url) = upload(results, public_key)
        return store_results(self.job_contract, url, hash_)

    def bulk_payout(self, payouts: List[Tuple[str, int]], results: Dict,
                    public_key: bytes) -> bool:
        """Performs a payout to multiple ethereum addresses.

        When the payout happens, final results are uploaded to IPFS and
        contract's state is updated.

        Args:
            payouts (List[Tuple[str, int]]): a list of tuples with ethereum addresses and amounts to pay.
            results (Dict): the final results of the job.
            public_key (bytes): the public key of the job requester or their agent.

        Returns:
            bool: returns True if bulk payout and IPFS upload succeeds.

        """
        (hash_, url) = upload(results, public_key)

        eth_addrs = [eth_addr for eth_addr, amount in payouts]
        amounts = [amount for eth_addr, amount in payouts]

        return _bulk_payout(self.job_contract, eth_addrs, amounts, url, hash_)

    def complete(self) -> bool:
        """Moves the Escrow solidity contract to a "Complete" state.

        Returns:
            bool: returns True if the contract is in "Complete" state.
        
        Raises:
            Exception: if contract was not in "Paid" or "Complete" state when called.
            
        """
        try:
            return _complete(self.job_contract)
        except Exception as e:
            LOG.error("Unable to complete contract:{} is the exception".format(
                str(e)))
            return False

    def get_manifest(self, private_key: bytes) -> Dict:
        """Retrieves the initial manifest used to setup the job.

        Args:
            private_key (bytes): the private key used to download the manifest.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        return download(_manifest_url(self.job_contract), private_key)

    def get_intermediate_results(self, private_key: bytes) -> Dict:
        """Retrieves the intermediate results.

        Args:
            private_key (bytes): the private key of the Reputation Oracle.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        return download(
            _intermediate_results_url(self.job_contract), private_key)

    def get_final_results(self, private_key: bytes) -> Dict:
        """Retrieves the final results.

        Args:
            private_key (bytes): the private key of the the job requester or their agent.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        return download(_final_results_url(self.job_contract), private_key)


def access_job(escrow_address: str, private_key: bytes) -> Contract:
    """Accesses an already deployed Escrow solidity contract and initializes an Escrow class
    based on the downloaded manifest from IPFS.

    Args:
        escrow_address (str): ethereum address of the deployed Escrow solidity contract.
        private_key (bytes): private key of the job requester or their agent.

    Returns:
        Escrow: returns the Escrow class with attributes initialized.

    """
    job = get_escrow(escrow_address)
    url = _manifest_url(job)
    manifest_dict = download(url, private_key)
    contract_manifest = Manifest(manifest_dict)
    contract = Contract(contract_manifest)
    contract.initialize(contract)
    return contract


def initialize_job() -> str:
    """Initialize a new job and launch it without funds on the blockchain.

    This is the first step of putting a new job on the blockchain.
    After this function is called the user can add funds, abort, or set the job up for pending.

    Returns:
        str: returns the address of the contract launched on the blockchain.

    """
    global FACTORY_ADDR
    factory = None

    if not FACTORY_ADDR:
        factory_address = deploy_factory()
        factory = get_factory(factory_address)
        FACTORY_ADDR = factory_address
        if not FACTORY_ADDR:
            raise Exception("Unable to get address from factory")

    if not factory:
        factory = get_factory(FACTORY_ADDR)
        counter = _counter(factory)
        LOG.debug("Factory counter is at:{}".format(counter))

    _create_escrow(factory)
    escrow_address = _last_address(factory)

    LOG.info("New Pokémon!:{}".format(escrow_address))
    return escrow_address


def setup_job(escrow: Escrow) -> bool:
    """Once a job hash been put on blockchain, and is funded, this function will
    setup the job for labeling (Pending):

    Args:
        escrow (Escrow): the Escrow object with initialized class attributes.

    Returns:
        bool: returns True if the contract is in "Pending" state.

    """

    return _setup(escrow)


def abort_job(escrow_contract: Contract) -> bool:
    """Return all leftover funds to the contract launcher and destroys the contract.

    Once a job hash been put on blockchain, and is funded, this function can return
    the money to the funder of the contract. This function cannot run if the contract
    is in "Partial" state.

    Args:
        escrow_contract (Contract): the deployed Escrow solidity contract.

    Returns:
        bool: returns True if the contract is in "Cancelled" state.
    
    """
    return _abort(escrow_contract)


def store_results(escrow_contract: Contract, intermediate_results_url: str,
                  intermediate_results_hash: str) -> bool:
    """Store intermediate results in the contract

    Args:
        escrow_contract (Contract): the deployed Escrow solidity contract.
        intermediate_results_url (str): The url of the answers to the questions.
        intermediate_results_hash (str): The hash of the plaintext of the manifest.

    Returns:
        bool: returns True if the results storage was successful
    
    """
    return _store_results(escrow_contract, intermediate_results_url,
                          intermediate_results_hash)


Status = Enum('Status', 'Launched Pending Partial Paid Complete Cancelled')


def status(escrow_contract: Contract) -> Enum:
    """User friendly status.

    Returns the status of an Escrow solidity contract:
    enum EscrowStatuses { Launched, Pending, Partial, Paid, Complete, Cancelled }

    Args:
        escrow_contract (Contract): the deployed Escrow solidity contract.

    Returns:
        Status: returns the enum which represents the state.

    """
    status_ = _status(escrow_contract)
    return Status(status_ + 1)
