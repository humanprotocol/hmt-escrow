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

GAS_LIMIT = int(os.getenv("GAS_LIMIT", 4712388))
FACTORY_ADDR = os.getenv("FACTORY_ADDR")

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
        factory = _check_factory(self)
        _create_escrow(self, factory)
        job_address = _last_address(self, factory)
        LOG.info("Job's escrow contract deployed to:{}".format(job_address))

        self.job_contract = get_escrow(job_address)
        (hash_, manifest_url) = upload(self.serialized_manifest, public_key)
        self.manifest_url = manifest_url
        self.manifest_hash = hash_
        return True

    def fund(self, gas: int = GAS_LIMIT) -> bool:
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
        hmtoken_contract = get_hmtoken()
        hmt_amount = int(self.amount * 10**18)

        w3 = get_w3()
        nonce = w3.eth.getTransactionCount(self.gas_payer)

        tx_dict = hmtoken_contract.functions.transfer(
            self.job_contract.address, hmt_amount).buildTransaction({
                'from':
                self.gas_payer,
                'gas':
                gas,
                'nonce':
                nonce
            })
        tx_hash = sign_and_send_transaction(tx_dict, self.gas_payer_priv)
        wait_on_transaction(tx_hash)
        return _balance(self) == hmt_amount

    def setup(self, gas: int = GAS_LIMIT) -> bool:
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
        reputation_oracle_stake = int(self.oracle_stake * 100)
        recording_oracle_stake = int(self.oracle_stake * 100)
        reputation_oracle = str(
            self.serialized_manifest["reputation_oracle_addr"])
        recording_oracle = str(
            self.serialized_manifest["recording_oracle_addr"])
        hmt_amount = int(self.amount * 10**18)

        w3 = get_w3()
        nonce = w3.eth.getTransactionCount(self.gas_payer)

        tx_dict = self.job_contract.functions.setup(
            reputation_oracle, recording_oracle, reputation_oracle_stake,
            recording_oracle_stake, hmt_amount, self.manifest_url,
            self.manifest_hash).buildTransaction({
                'from': self.gas_payer,
                'gas': gas,
                'nonce': nonce
            })
        tx_hash = sign_and_send_transaction(tx_dict, self.gas_payer_priv)
        wait_on_transaction(tx_hash)
        return self.status(gas) == Status.Pending

    def bulk_payout(self,
                    payouts: List[Tuple[str, Decimal]],
                    results: Dict,
                    public_key: bytes,
                    gas: int = GAS_LIMIT) -> bool:
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
        >>> job.status()
        <Status.Partial: 3>

        Trying to pay more than the contract balance results in failure.
        >>> payouts = [("0x9d689b8f50Fd2CAec716Cc5220bEd66E03F07B5f", Decimal('40.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        False

        >>> payouts = [("0x9d689b8f50Fd2CAec716Cc5220bEd66E03F07B5f", Decimal('30.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True
        >>> _balance(job)
        0
        >>> job.status()
        <Status.Paid: 4>

        Args:
            payouts (List[Tuple[str, int]]): a list of tuples with ethereum addresses and amounts.
            results (Dict): the final answer results stored by the Reputation Oracle.
            public_key (bytes): the public key of the Reputation Oracle.

        Returns:
            bool: returns True if paying to ethereum addresses and oracles succeeds.

        """
        (hash_, url) = upload(results, public_key)

        eth_addrs = [eth_addr for eth_addr, amount in payouts]
        hmt_amounts = [int(amount * 10**18) for eth_addr, amount in payouts]

        w3 = get_w3()
        nonce = w3.eth.getTransactionCount(self.gas_payer)

        tx_dict = self.job_contract.functions.bulkPayOut(
            eth_addrs, hmt_amounts, url, hash_, 1).buildTransaction({
                'from':
                self.gas_payer,
                'gas':
                gas,
                'nonce':
                nonce
            })
        tx_hash = sign_and_send_transaction(tx_dict, self.gas_payer_priv)
        wait_on_transaction(tx_hash)
        return _bulk_paid(self) == True

    def abort(self, gas: int = GAS_LIMIT) -> bool:
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
        >>> job.status()
        <Status.Partial: 3>

        The escrow contract is in Paid state after the second payout and it can't be aborted.
        >>> payouts = [("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('80.0'))]
        >>> job.bulk_payout(payouts, {'results': 0}, rep_oracle_pub_key)
        True
        >>> job.abort()
        False
        >>> job.status()
        <Status.Paid: 4>
            
        Returns:
            bool: returns True if contract has been destroyed successfully.

        """
        w3 = get_w3()
        nonce = w3.eth.getTransactionCount(self.gas_payer)

        tx_dict = self.job_contract.functions.abort().buildTransaction({
            'from':
            self.gas_payer,
            'gas':
            gas,
            'nonce':
            nonce
        })
        tx_hash = sign_and_send_transaction(tx_dict, self.gas_payer_priv)
        wait_on_transaction(tx_hash)

        # After abort the contract should be destroyed
        contract_code = w3.eth.getCode(self.job_contract.address)
        return contract_code == b"\x00"

    def cancel(self, gas: int = GAS_LIMIT) -> bool:
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
        >>> job.status()
        <Status.Cancelled: 6>

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
        >>> job.status()
        <Status.Partial: 3>

        The escrow contract is in Paid state after the second payout and it can't be cancelled.
        >>> payouts = [("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('80.0'))]
        >>> job.bulk_payout(payouts, {'results': 0}, rep_oracle_pub_key)
        True
        >>> job.cancel()
        False
        >>> job.status()
        <Status.Paid: 4>

        Returns:
            bool: returns True if gas payer has been paid back and contract is in "Cancelled" state.

        """
        w3 = get_w3()
        nonce = w3.eth.getTransactionCount(self.gas_payer)

        tx_dict = self.job_contract.functions.cancel().buildTransaction({
            'from':
            self.gas_payer,
            'gas':
            gas,
            'nonce':
            nonce
        })
        tx_hash = sign_and_send_transaction(tx_dict, self.gas_payer_priv)
        wait_on_transaction(tx_hash)

        return self.status(gas) == Status.Cancelled

    def status(self, gas: int = GAS_LIMIT) -> Enum:
        """Returns the status of a contract.

        Returns:
            Enum: returns the status as an enumeration.

        """
        status_ = self.job_contract.functions.getStatus().call({
            'from':
            self.gas_payer,
            'gas':
            gas
        })
        return Status(status_ + 1)

    def store_intermediate_results(self,
                                   results: Dict,
                                   public_key: bytes,
                                   gas: int = GAS_LIMIT) -> bool:
        """Stores intermediate results with Reputation Oracle's public key to IPFS.

        Args:
            results (Dict): intermediate results of the Recording Oracle.
            public_key (bytes): public key of the Reputation Oracle.
        
        Returns:
            returns True if contract's state is updated and IPFS upload succeeds.

        """
        (hash_, url) = upload(results, public_key)

        w3 = get_w3()
        nonce = w3.eth.getTransactionCount(self.gas_payer)

        tx_dict = self.job_contract.functions.storeResults(
            url, hash_).buildTransaction({
                'from': self.gas_payer,
                'gas': gas,
                'nonce': nonce
            })
        tx_hash = sign_and_send_transaction(tx_dict, self.gas_payer_priv)
        wait_on_transaction(tx_hash)
        return True

    def complete(self, gas: int = GAS_LIMIT) -> bool:
        """Moves the Job solidity contract to a "Complete" state.

        Returns:
            bool: returns True if the contract is in "Complete" state.
        
        Raises:
            Exception: if contract was not in "Paid" or "Complete" state when called.
            
        """
        try:
            w3 = get_w3()
            nonce = w3.eth.getTransactionCount(self.gas_payer)

            tx_dict = self.job_contract.functions.complete().buildTransaction({
                'from':
                self.gas_payer,
                'gas':
                gas,
                'nonce':
                nonce
            })
            tx_hash = sign_and_send_transaction(tx_dict, self.gas_payer_priv)
            wait_on_transaction(tx_hash)
            return self.status() == Status.Complete
        except Exception as e:
            LOG.error("Unable to complete contract:{} is the exception".format(
                str(e)))
            return False

    def manifest(self, private_key: bytes) -> Dict:
        """Retrieves the initial manifest used to setup the job.

        Args:
            private_key (bytes): the private key used to download the manifest.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        return download(_manifest_url(self, self.gas_payer), private_key)

    def intermediate_results(self, private_key: bytes,
                             gas: int = GAS_LIMIT) -> Dict:
        """Retrieves the intermediate results.

        Args:
            private_key (bytes): the private key of the Reputation Oracle.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        intermediate_results_url = self.job_contract.functions.getIntermediateResultsUrl(
        ).call({
            'from': self.gas_payer,
            'gas': gas
        })
        return download(intermediate_results_url, private_key)

    def final_results(self, private_key: bytes, gas: int = GAS_LIMIT) -> Dict:
        """Retrieves the final results.

        Args:
            private_key (bytes): the private key of the the job requester or their agent.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        final_results_url = self.job_contract.functions.getFinalResultsUrl(
        ).call({
            'from': self.gas_payer,
            'gas': gas
        })
        return download(final_results_url, private_key)


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


def _balance(job: Job, gas: int = GAS_LIMIT) -> int:
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


def _bulk_paid(job: Job, gas: int = GAS_LIMIT) -> int:
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    return escrow_contract.functions.getBulkPaid().call({
        'from': gas_payer,
        'gas': gas
    })


def _check_factory(job: Job, gas: int = GAS_LIMIT) -> Contract:
    gas_payer = job.gas_payer
    gas_payer_priv = job.gas_payer_priv

    global FACTORY_ADDR
    factory_address_valid = Web3.isChecksumAddress(FACTORY_ADDR)
    factory = None

    if not factory_address_valid:
        factory_address = deploy_factory(gas_payer, gas_payer_priv)
        factory = get_factory(factory_address)
        FACTORY_ADDR = factory_address
        if not FACTORY_ADDR:
            raise Exception("Unable to get address from factory")

    if not factory:
        factory = get_factory(Web3.toChecksumAddress(FACTORY_ADDR))
        counter = _counter(job, factory)
        LOG.debug("Factory counter is at:{}".format(counter))
    return factory


def _counter(job: Job, factory_contract: Contract,
             gas: int = GAS_LIMIT) -> int:
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
                  gas: int = GAS_LIMIT) -> str:
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


def _create_escrow(job: Job, factory_contract: Contract,
                   gas: int = GAS_LIMIT) -> bool:
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
                  gas: int = GAS_LIMIT) -> str:
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
    doctest.testmod()
