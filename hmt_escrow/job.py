#!/usr/bin/env python3
import os
import logging

from decimal import *
from enum import Enum
from typing import Dict, List, Tuple

from web3 import Web3
from web3.contract import Contract
from eth_keys import keys
from eth_utils import decode_hex

from eth_bridge import get_hmtoken, get_contract_interface, wait_on_transaction, get_escrow, get_factory, deploy_factory, get_w3, sign_and_send_transaction
from storage import download, upload
from basemodels import Manifest

DEFAULT_GAS = int(os.getenv("DEFAULT_GAS", 4712388))
FACTORY_ADDR = os.getenv("FACTORY_ADDR")
if FACTORY_ADDR:
    FACTORY_ADDR = Web3.toChecksumAddress(FACTORY_ADDR)

LOG = logging.getLogger("hmt_escrow")
Status = Enum('Status', 'Launched Pending Partial Paid Complete Cancelled')


class Job:
    """A class used to represent a given Job launched on the HUMAN network.
    A Job  can be created from a manifest or by accessing an existing escrow contract 
    from the Ethereum network with the external access_job function. The manifest
    has to follow the Manifest model specification at https://github.com/hCaptcha/hmt-basemodels.

    A typical Job goes through the following stages:
    Deploy: deploy an escrow contract to the network.
    Fund: store HMT in the contract.
    Setup: store relevant attributes in the contract state.
    Pay: pay all websites in HMT when all the Job's tasks have been completed.

    Attributes:
        serialized_manifest (Dict[str, Any]): a dict representation of the Manifest model.
        gas_payer (str): an ethereum address paying for the gas costs.
        gas_payer_priv (str): the private key of the gas_payer.
        amount (Decimal): an amount to be stored in the escrow contract.
        oracle_stake (Decimal): a percentage the Reputation and Recording Oracles get.
        manifest_url (str): the location of the serialized manifest in IPFS.
        manifest_hash (str): SHA-1 hashed version of the serialized manifest.

    """

    def __init__(self, manifest: Manifest, gas_payer: str,
                 gas_payer_priv: str):
        """Initializes a Job instance with values from a Manifest class and 
        checks that the provided credentials are valid.

        Examples:
        >>> gas_payer = "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92"
        >>> gas_payer_priv = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> job = Job(test_manifest(), gas_payer, gas_payer_priv)
        >>> job.gas_payer == gas_payer
        True
        >>> job.gas_payer_priv == gas_payer_priv
        True
        >>> job.oracle_stake
        Decimal('0.05')
        >>> job.amount
        Decimal('100.0')

        Args:
            manifest (Manifest): an instance of the Manifest class.
            gas_payer (str): an ethereum address paying for the gas costs.
            gas_payer_priv (str): the private key of the gas_payer.
        
        Raises:
            Exception: if the Job has been already initialized.
            ValueError: if the credentials are not valid.

        """
        credentials_valid = _validate_credentials(gas_payer, gas_payer_priv)
        if not credentials_valid:
            raise ValueError("Given private key doesn't match the address")

        serialized_manifest = dict(manifest.serialize())
        per_job_cost = Decimal(serialized_manifest['task_bid_price'])
        number_of_answers = int(serialized_manifest['job_total_tasks'])
        oracle_stake = Decimal(serialized_manifest["oracle_stake"])

        self.serialized_manifest = serialized_manifest
        self.gas_payer = Web3.toChecksumAddress(gas_payer)
        self.gas_payer_priv = gas_payer_priv
        self.oracle_stake = oracle_stake
        self.amount = Decimal(per_job_cost * number_of_answers)

    def deploy(self, public_key: bytes) -> bool:
        """Launches an escrow contract to the network, uploads the manifest
        to IPFS with the public key of the Reputation Oracle and stores 
        the IPFS url to the escrow contract.

        Examples:
        >>> gas_payer = "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92"
        >>> gas_payer_priv = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> rep_oracle_pub_key = b'94e67e63b2bf9b960b5a284aef8f4cc2c41ce08b083b89d17c027eb6f11994140d99c0aeadbf32fbcdac4785c5550bf28eefd0d339c74a033d55b1765b6503bf'
        >>> job = Job(test_manifest(), gas_payer, gas_payer_priv)
        >>> job.deploy(rep_oracle_pub_key)
        True

        Args:
            public_key (bytes): the public key of the Reputation Oracle.

        Returns:
            bool: returns True if Class initialization and Ethereum and IPFS transactions succeed.

        """
        job_address = _initialize(self)
        self.job_contract = get_escrow(job_address)
        (hash_, manifest_url) = upload(self.serialized_manifest, public_key)
        self.manifest_url = manifest_url
        self.manifest_hash = hash_
        return True

    def fund(self) -> bool:
        """Funds the escrow contract with the amount in Job's class attributes.
        The contract needs to be deployed first.

        >>> gas_payer = "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92"
        >>> gas_payer_priv = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> rep_oracle_pub_key = b'94e67e63b2bf9b960b5a284aef8f4cc2c41ce08b083b89d17c027eb6f11994140d99c0aeadbf32fbcdac4785c5550bf28eefd0d339c74a033d55b1765b6503bf'

        We can't fund a job without deploying it first.
        >>> job = Job(test_manifest(), gas_payer, gas_payer_priv)
        >>> job.fund()
        Traceback (most recent call last):
        AttributeError: 'Job' object has no attribute 'job_contract'

        >>> job.deploy(rep_oracle_pub_key)
        True
        >>> job.fund()
        True

        Returns:
            bool: returns True if contract is funded with Job's amount.
        
        Raises:
            AttributeError: if trying to fund the job before deploying it.

        """
        return _fund(self)

    def setup(self) -> bool:
        """Sets the escrow contract to be ready to receive answers from the Recording Oracle.
        The contract needs to be deployed and funded first.

        >>> gas_payer = "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92"
        >>> gas_payer_priv = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> rep_oracle_pub_key = b'94e67e63b2bf9b960b5a284aef8f4cc2c41ce08b083b89d17c027eb6f11994140d99c0aeadbf32fbcdac4785c5550bf28eefd0d339c74a033d55b1765b6503bf'

        >>> job = Job(test_manifest(), gas_payer, gas_payer_priv)

        We can't setup a job without deploying it first.
        >>> job.setup()
        Traceback (most recent call last):
        AttributeError: 'Job' object has no attribute 'job_contract'

        >>> job.deploy(rep_oracle_pub_key)
        True

        We can't setup a job without funding it first.
        >>> job.setup()
        False

        >>> job.fund()
        True
        >>> job.setup()
        True

        Returns:
            bool: returns True if Job is in Pending state.
        
        Raises:
            AttributeError: if trying to setup the job before deploying it.

        """
        return _setup(self)

    def bulk_payout(self, payouts: List[Tuple[str, Decimal]], results: Dict,
                    public_key: bytes) -> bool:
        """Performs a payout to multiple ethereum addresses. When the payout happens,
        final results are uploaded to IPFS and contract's state is updated to Partial or Paid
        depending on contract's balance.

        >>> gas_payer = "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92"
        >>> gas_payer_priv = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> rep_oracle_pub_key = b'94e67e63b2bf9b960b5a284aef8f4cc2c41ce08b083b89d17c027eb6f11994140d99c0aeadbf32fbcdac4785c5550bf28eefd0d339c74a033d55b1765b6503bf'

        >>> job = Job(test_manifest(), gas_payer, gas_payer_priv)
        >>> job.deploy(rep_oracle_pub_key)
        True
        >>> job.fund()
        True
        >>> job.setup()
        True
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0')), ("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('50.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True

        The escrow contract is still in Partial state as there's still balance left.
        >>> _balance(job)
        30000000000000000000
        >>> _status(job)
        2

        Trying to pay more than the contract balance results in failure.
        >>> payouts = [("0x9d689b8f50Fd2CAec716Cc5220bEd66E03F07B5f", Decimal('40.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        False

        >>> payouts = [("0x9d689b8f50Fd2CAec716Cc5220bEd66E03F07B5f", Decimal('30.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True
        >>> _balance(job)
        0
        >>> _status(job)
        3

        Args:
            payouts (List[Tuple[str, int]]): a list of tuples with ethereum addresses and amounts.
            results (Dict): the final answer results stored by the Reputation Oracle.
            public_key (bytes): the public key of the Reputation Oracle.

        Returns:
            bool: returns True if paying to ethereum addresses and oracles succeeds.

        """
        (hash_, url) = upload(results, public_key)

        eth_addrs = [eth_addr for eth_addr, amount in payouts]
        amounts = [amount for eth_addr, amount in payouts]

        return _bulk_payout(self, eth_addrs, amounts, url, hash_)

    def abort(self) -> bool:
        """Kills the contract and returns the HMT back to the gas payer.
        The contract cannot be aborted if the contract is in Partial, Paid or Complete state.

        >>> gas_payer = "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92"
        >>> gas_payer_priv = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> rep_oracle_pub_key = b'94e67e63b2bf9b960b5a284aef8f4cc2c41ce08b083b89d17c027eb6f11994140d99c0aeadbf32fbcdac4785c5550bf28eefd0d339c74a033d55b1765b6503bf'

        The escrow contract is in Pending state after setup so it can be aborted.
        >>> job = Job(test_manifest(), gas_payer, gas_payer_priv)
        >>> job.deploy(rep_oracle_pub_key)
        True
        >>> job.fund()
        True
        >>> job.setup()
        True
        >>> job.abort()
        True

        The escrow contract is in Partial state after the first payout and it can't be aborted.
        >>> job = Job(test_manifest(), gas_payer, gas_payer_priv)
        >>> job.deploy(rep_oracle_pub_key)
        True
        >>> job.fund()
        True
        >>> job.setup()
        True
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True
        >>> job.abort()
        False
        >>> _status(job)
        2

        The escrow contract is in Paid state after the second payout and it can't be aborted.
        >>> payouts = [("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('80.0'))]
        >>> job.bulk_payout(payouts, {'results': 0}, rep_oracle_pub_key)
        True
        >>> job.abort()
        False
        >>> _status(job)
        3
            
        Returns:
            bool: returns True if contract has been destroyed successfully.

        """
        return _abort(self)

    def cancel(self) -> bool:
        """Returns the HMT back to the gas payer. It's the softer version of abort as the contract is not destroyed.

        >>> gas_payer = "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92"
        >>> gas_payer_priv = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> rep_oracle_pub_key = b'94e67e63b2bf9b960b5a284aef8f4cc2c41ce08b083b89d17c027eb6f11994140d99c0aeadbf32fbcdac4785c5550bf28eefd0d339c74a033d55b1765b6503bf'

        The escrow contract is in Pending state after setup so it can be cancelled.
        >>> job = Job(test_manifest(), gas_payer, gas_payer_priv)
        >>> job.deploy(rep_oracle_pub_key)
        True
        >>> job.fund()
        True
        >>> job.setup()
        True
        >>> job.cancel()
        True

        Contract balance is zero and status is "Cancelled".
        >>> _balance(job)
        0
        >>> _status(job)
        5

        The escrow contract is in Partial state after the first payout and it can't be cancelled.
        >>> job = Job(test_manifest(), gas_payer, gas_payer_priv)
        >>> job.deploy(rep_oracle_pub_key)
        True
        >>> job.fund()
        True
        >>> job.setup()
        True
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True
        >>> job.cancel()
        False
        >>> _status(job)
        2

        The escrow contract is in Paid state after the second payout and it can't be cancelled.
        >>> payouts = [("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('80.0'))]
        >>> job.bulk_payout(payouts, {'results': 0}, rep_oracle_pub_key)
        True
        >>> job.cancel()
        False
        >>> _status(job)
        3

        Returns:
            bool: returns True if gas payer has been paid back and contract is in "Cancelled" state.

        """
        return _cancel(self)

    def status(self) -> Enum:
        """Returns the status of a contract.

        Returns:
            Enum: returns the status as an enumeration.

        """
        status_ = _status(self)
        return Status(status_ + 1)

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
        return _store_intermediate_results(self, url, hash_)

    def complete(self) -> bool:
        """Moves the Job solidity contract to a "Complete" state.

        Returns:
            bool: returns True if the contract is in "Complete" state.
        
        Raises:
            Exception: if contract was not in "Paid" or "Complete" state when called.
            
        """
        try:
            return _complete(self)
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
        return download(_manifest_url(self, self.gas_payer), private_key)

    def get_intermediate_results(self, private_key: bytes) -> Dict:
        """Retrieves the intermediate results.

        Args:
            private_key (bytes): the private key of the Reputation Oracle.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        return download(_intermediate_results_url(self), private_key)

    def get_final_results(self, private_key: bytes) -> Dict:
        """Retrieves the final results.

        Args:
            private_key (bytes): the private key of the the job requester or their agent.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        return download(_final_results_url(self), private_key)


def _validate_credentials(address: str, private_key: str) -> bool:
    """Validates whether the given ethereum private key maps to the address
    by calculating the checksum address from the private key and comparing that
    to the given address.

    Tests:
    >>> _validate_credentials("0x1413862C2B7054CDbfdc181B83962CB0FC11fD92", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5")
    True

    Args:
        address (str): 42 characters long ethereum address.
        private_key (str): 64 characters long private key.
    
    Returns:
        bool: returns True if the calculated and the given address match.

    """
    priv_key_bytes = decode_hex(private_key)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    calculated_address = pub_key.to_checksum_address()
    return Web3.toChecksumAddress(address) == calculated_address


def _status(job: Job, gas: int = DEFAULT_GAS) -> int:
    """Wrapper function that calls Job solidity contract's getStatus method in a read-only manner.

    Enums:
        0: Launched
        1: Pending
        2: Partial
        3: Paid
        4: Complete
        5: Cancelled

    Args:
        escrow_contract (Contract): the contract to be read.
        gas_payer (str): an ethereum address paying the gas costs.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        int: returns the number equivalent to the status of the contract.

    """
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    return escrow_contract.functions.getStatus().call({
        'from': gas_payer,
        'gas': gas
    })


def _intermediate_results_url(job: Job, gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls Job solidity contract's getIntermediateResultsUrl method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the intermediate results url

    """
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    return escrow_contract.functions.getIntermediateResultsUrl().call({
        'from':
        gas_payer,
        'gas':
        gas
    })


def _final_results_url(job: Job, gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls Job solidity contract's getFinalResultsUrl method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the final results url

    """
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    return escrow_contract.functions.getFinalResultsUrl().call({
        'from':
        gas_payer,
        'gas':
        gas
    })


def _balance(job: Job, gas: int = DEFAULT_GAS) -> int:
    """Wrapper function that calls Job solidity contract's getBalance method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        int: returns the balance of the contract.

    """
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    return escrow_contract.functions.getBalance().call({
        'from': gas_payer,
        'gas': gas
    })


def _bulk_paid(job: Job, gas: int = DEFAULT_GAS) -> int:
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    return escrow_contract.functions.getBulkPaid().call({
        'from': gas_payer,
        'gas': gas
    })


def _bulk_payout(job: Job,
                 addresses: List[str],
                 amounts: List[Decimal],
                 uri: str,
                 hash_: str,
                 gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Job solidity contract's bulkPayout method that creates a transaction to the network.

    Handles the conversion of the oracle_stake and fundable amount to contract's native values.
    amount: Multiply by 10^18 to get the correct amount in HMT dictated by solidity contract's decimals.

    Args:
        escrow_contract (Contract): the contract to be updated.
        addresses (list): ethereum addresses receiving payouts.
        amounts (list): corresponding list of HMT to be paid.
        uri (str): final manifest result url getting updated to the Job solidity contract's state.
        hash_ (str): final manifest result hash getting updated to the Job solidity contract's state.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if the payout was successful.
    
    Raises:
        TimeoutError: if wait_on_transaction times out.

    """
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    gas_payer_priv = job.gas_payer_priv

    hmt_amounts = [int(amount * 10**18) for amount in amounts]

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(gas_payer)

    tx_dict = escrow_contract.functions.bulkPayOut(addresses, hmt_amounts, uri,
                                                   hash_, 1).buildTransaction({
                                                       'from':
                                                       gas_payer,
                                                       'gas':
                                                       gas,
                                                       'nonce':
                                                       nonce
                                                   })
    tx_hash = sign_and_send_transaction(tx_dict, gas_payer_priv)
    wait_on_transaction(tx_hash)
    return _bulk_paid(job) == True


def _store_intermediate_results(job: Job,
                                uri: str,
                                hash_: str,
                                gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Job solidity contract's storeResults method that creates a transaction to the network.

    Args:
        escrow_contract (Contract): the contract to be updated.
        uri (str): intermediate manifest result url getting updated to the Job solidity contract's state.
        hash_ (str): intermediate manifest result hash getting updated to the Job solidity contract's state.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if intermediate results were successfully updated
    
    Raises:
        TimeoutError: if wait_on_transaction times out

    """
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    gas_payer_priv = job.gas_payer_priv

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(gas_payer)

    tx_dict = escrow_contract.functions.storeResults(uri,
                                                     hash_).buildTransaction({
                                                         'from':
                                                         gas_payer,
                                                         'gas':
                                                         gas,
                                                         'nonce':
                                                         nonce
                                                     })
    tx_hash = sign_and_send_transaction(tx_dict, gas_payer_priv)
    wait_on_transaction(tx_hash)
    return True


def _complete(job: Job, gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Job solidity contract's complete method that creates a transaction to the network.

    Makes a separate call to check the status of the contract by using internal helper function _status.

    Args:
        escrow_contract (Contract): the contract to be updated.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Complete" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out

    """
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    gas_payer_priv = job.gas_payer_priv

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(gas_payer)

    tx_dict = escrow_contract.functions.complete().buildTransaction({
        'from':
        gas_payer,
        'gas':
        gas,
        'nonce':
        nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, gas_payer_priv)
    wait_on_transaction(tx_hash)
    return _status(job) == 4


def _abort(job: Job, gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Job solidity contract's abort method that creates a transaction to the network.

    Makes a separate call to check the status of the contract by using internal helper function _status.

    Args:
        escrow_contract (Contract): the contract to be updated.
        gas_payer (str): an ethereum address paying the gas costs.
        gas_payer_priv (str): the private key of the gas payer.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Cancelled" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out

    """
    escrow_contract = job.job_contract
    escrow_address = escrow_contract.address
    gas_payer = job.gas_payer
    gas_payer_priv = job.gas_payer_priv

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(gas_payer)

    tx_dict = escrow_contract.functions.abort().buildTransaction({
        'from':
        gas_payer,
        'gas':
        gas,
        'nonce':
        nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, gas_payer_priv)
    wait_on_transaction(tx_hash)

    # After abort the contract should be destroyed
    contract_code = w3.eth.getCode(escrow_address)
    return contract_code == b"\x00"


def _cancel(job: Job, gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Job solidity contract's refund method that creates a transaction to the network.

    Makes a separate call to check the status of the contract by using internal helper function _status.

    Args:
        escrow_contract (Contract): the contract to be updated.
        gas_payer (str): an ethereum address paying the gas costs.
        gas_payer_priv (str): the private key of the gas payer.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Cancelled" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out

    """
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    gas_payer_priv = job.gas_payer_priv

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(gas_payer)

    tx_dict = escrow_contract.functions.cancel().buildTransaction({
        'from':
        gas_payer,
        'gas':
        gas,
        'nonce':
        nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, gas_payer_priv)
    wait_on_transaction(tx_hash)

    return _status(job) == 5


def _setup(job: Job, gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls Job solidity contract's setup method that creates a transaction to the network.

    Handles the conversion of the oracle_stake and fundable amount to contract's native values:
    oracle_stake: Multiply by 100 to an integer value between 0 and 100.
    amount: Multiply by 10^18 to get the correct amount in HMT dictated by solidity contract's decimals.

    Args:
        job (Job): the Job class preferrably already initialized
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Pending" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out.

    """
    escrow_contract = job.job_contract
    reputation_oracle_stake = int(job.oracle_stake * 100)
    recording_oracle_stake = int(job.oracle_stake * 100)
    reputation_oracle = str(job.serialized_manifest["reputation_oracle_addr"])
    recording_oracle = str(job.serialized_manifest["recording_oracle_addr"])
    manifest_url = job.manifest_url
    manifest_hash = job.manifest_hash
    hmt_amount = int(job.amount * 10**18)

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(job.gas_payer)

    tx_dict = escrow_contract.functions.setup(
        reputation_oracle, recording_oracle, reputation_oracle_stake,
        recording_oracle_stake, hmt_amount, manifest_url,
        manifest_hash).buildTransaction({
            'from': job.gas_payer,
            'gas': gas,
            'nonce': nonce
        })
    tx_hash = sign_and_send_transaction(tx_dict, job.gas_payer_priv)
    wait_on_transaction(tx_hash)
    return _status(job) == 1


def _initialize(job: Job) -> str:
    """Initialize a new job and launch it without funds on the blockchain.

    This is the first step of putting a new job on the blockchain.
    After this function is called the user can add funds, abort, or set the job up for pending.

    Returns:
        str: returns the address of the contract launched on the blockchain.

    """
    gas_payer = job.gas_payer
    gas_payer_priv = job.gas_payer_priv

    global FACTORY_ADDR
    factory = None

    if not FACTORY_ADDR:
        factory_address = deploy_factory(gas_payer, gas_payer_priv)
        factory = get_factory(factory_address)
        FACTORY_ADDR = factory_address
        if not FACTORY_ADDR:
            raise Exception("Unable to get address from factory")

    if not factory:
        factory = get_factory(FACTORY_ADDR)
        counter = _counter(job, factory)
        LOG.debug("Factory counter is at:{}".format(counter))

    _create_escrow(job, factory)
    escrow_address = _last_address(job, factory)

    LOG.info("New Pokémon!:{}".format(escrow_address))
    return escrow_address


def _fund(job: Job, gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls HMToken solidity contract's transfer method that creates a transaction to the network.

    Handles the conversion of the oracle_stake and fundable amount to contract's native values:
    amount: Multiply by 10^18 to get the correct amount in HMT dictated by solidity contract's decimals.

    Args:
        address (str): an ethereum address to receive HMT.
        amount (Decimal): the amount of HMT to be paid before the decimal conversion.
        gas_payer (str): an ethereum address paying the gas costs.
        gas_payer_priv (str): the private key of the gas payer.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if contract's status is in "Pending" state.
    
    Raises:
        TimeoutError: if wait_on_transaction times out.

    """
    address = job.job_contract.address
    amount = job.amount
    gas_payer = job.gas_payer
    gas_payer_priv = job.gas_payer_priv

    hmtoken_contract = get_hmtoken()
    hmt_amount = int(amount * 10**18)

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(gas_payer)

    tx_dict = hmtoken_contract.functions.transfer(
        address, hmt_amount).buildTransaction({
            'from': gas_payer,
            'gas': gas,
            'nonce': nonce
        })
    tx_hash = sign_and_send_transaction(tx_dict, gas_payer_priv)
    wait_on_transaction(tx_hash)
    return _balance(job) == hmt_amount


def _counter(job: Job, factory_contract: Contract,
             gas: int = DEFAULT_GAS) -> int:
    """Wrapper function that calls EscrowFactory solidity contract's getCounter method in a read-only manner.

    Args:
        factory_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        int: returns the balance of the contract

    """
    gas_payer = job.gas_payer
    return factory_contract.functions.getCounter().call({
        'from': gas_payer,
        'gas': gas
    })


def _last_address(job: Job, factory_contract: Contract,
                  gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls EscrowFactory solidity contract's getLastAddress method in a read-only manner.

    Args:
        factory_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the last address of an job contract deployed by EscrowFactory

    """
    gas_payer = job.gas_payer
    return factory_contract.functions.getLastAddress().call({
        'from': gas_payer,
        'gas': gas
    })


def _create_escrow(job: Job,
                   factory_contract: Contract,
                   gas: int = DEFAULT_GAS) -> bool:
    """Wrapper function that calls EscrowFactory solidity contract's createEscrow method that creates a transaction to the network.

    Args:
        factory_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if a new job (Pokémon) was successfully launched to the network.
    
    Raises:
        TimeoutError: if wait_on_transaction times out.

    """
    gas_payer = job.gas_payer
    gas_payer_priv = job.gas_payer_priv

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(gas_payer)
    tx_dict = factory_contract.functions.createEscrow().buildTransaction({
        'from':
        gas_payer,
        'gas':
        gas,
        'nonce':
        nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, gas_payer_priv)
    wait_on_transaction(tx_hash)
    return True


def _manifest_url(escrow_contract: Contract,
                  gas_payer: str,
                  gas: int = DEFAULT_GAS) -> str:
    """Wrapper function that calls Job solidity contract's getManifestUrl method in a read-only manner.

    Args:
        escrow_contract (Contract): the contract to be read.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns the manifest url

    """
    return escrow_contract.functions.getManifestUrl().call({
        'from': gas_payer,
        'gas': gas
    })


def access_job(escrow_address: str, gas_payer: str, gas_payer_priv: str,
               private_key: bytes) -> Contract:
    """Accesses an already deployed Job solidity contract and initializes an Job class
    based on the downloaded manifest from IPFS.

    Args:
        escrow_address (str): ethereum address of the deployed Job solidity contract.
        private_key (bytes): private key of the job requester or their agent.

    Returns:
        Job: returns the Job class with attributes initialized.

    """
    job = get_escrow(escrow_address)
    url = _manifest_url(job, gas_payer)
    manifest_dict = download(url, private_key)
    escrow_manifest = Manifest(manifest_dict)
    job = Job(escrow_manifest, gas_payer, gas_payer_priv)
    return job


if __name__ == "__main__":
    import doctest
    from test_job import test_manifest
    from storage import upload
    from unittest.mock import MagicMock
    doctest.testmod()
