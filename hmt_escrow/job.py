#!/usr/bin/env python3
import os
import sys
import logging
import timeout_decorator
import ipfsapi

# For accessing hmt_escrow files locally.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import *
from enum import Enum
from typing import Dict, List, Tuple, Optional

from web3 import Web3
from web3.contract import Contract
from eth_keys import keys
from eth_utils import decode_hex

from ipfsapi import Client
from hmt_escrow.eth_bridge import get_hmtoken, get_contract_interface, get_escrow, get_factory, deploy_factory, get_w3, handle_transaction
from hmt_escrow.storage import download, upload
from basemodels import Manifest

GAS_LIMIT = int(os.getenv("GAS_LIMIT", 4712388))
IPFS_HOST = os.getenv("IPFS_HOST", "localhost")
IPFS_PORT = int(os.getenv("IPFS_PORT", 5001))

LOG = logging.getLogger("hmt_escrow.job")
Status = Enum('Status', 'Launched Pending Partial Paid Complete Cancelled')


class Job:
    """A class used to represent a given Job launched on the HUMAN network.
    A Job  can be created from a manifest or by accessing an existing escrow contract 
    from the Ethereum network. The manifest has to follow the Manifest model 
    specification at https://github.com/hCaptcha/hmt-basemodels.

    A typical Job goes through the following stages:
    Launch: deploy an escrow contract to the network.
    Setup: store relevant attributes in the contract state.
    Pay: pay all job participatants in HMT when all the Job's tasks have been completed.

    Attributes:
        serialized_manifest (Dict[str, Any]): a dict representation of the Manifest model.
        factory_contract (Contract): the factory contract used to create Job's escrow contract.
        job_contract (Contract): the escrow contract of the Job.
        gas_payer (str): an ethereum address paying for the gas costs.
        gas_payer_priv (str): the private key of the gas_payer.
        amount (Decimal): an amount to be stored in the escrow contract.
        manifest_url (str): the location of the serialized manifest in IPFS.
        manifest_hash (str): SHA-1 hashed version of the serialized manifest.

    """

    def __init__(self,
                 credentials: Dict[str, str],
                 escrow_manifest: Manifest = None,
                 factory_addr: str = None,
                 escrow_addr: str = None,
                 ipfs_client: Client = None):
        """Initializes a Job instance with values from a Manifest class and 
        checks that the provided credentials are valid. An optional factory
        address is used to initialize the factory of the Job. Alternatively
        a new factory is created if no factory address is provided.

        Creating a new Job instance initializes the critical attributes correctly.
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.gas_payer == credentials["gas_payer"]
        True
        >>> job.gas_payer_priv == credentials["gas_payer_priv"]
        True
        >>> job.serialized_manifest["oracle_stake"]
        '0.05'
        >>> job.amount
        Decimal('100.0')

        Initializing a new Job instance with a factory address succeeds.
        >>> factory_addr = deploy_factory(**credentials)
        >>> job = Job(credentials, manifest, factory_addr)
        >>> job.factory_contract.address == factory_addr
        True
        
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True

        Initializing an existing Job instance with a factory and escrow address succeeds.
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        ...     "rep_oracle_priv_key": b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> escrow_addr = job.job_contract.address
        >>> factory_addr = job.factory_contract.address
        >>> manifest_url = job._manifest_url()

        >>> new_job = Job(credentials=credentials, factory_addr=factory_addr, escrow_addr=escrow_addr)
        >>> new_job.manifest_url == manifest_url
        True
        >>> new_job.job_contract.address == escrow_addr
        True
        >>> new_job.factory_contract.address == factory_addr
        True
        >>> new_job.launch(rep_oracle_pub_key)
        Traceback (most recent call last):
        AttributeError: The escrow has been already deployed.

        Creating a new Job instance with falsy credentials fails.
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"
        ... }
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        Traceback (most recent call last):
        ValueError: Given private key doesn't match the ethereum address.

        Args:
            manifest (Manifest): an instance of the Manifest class.
            credentials (Dict[str, str]): an ethereum address and its private key.
            factory_addr (str): an ethereum address of the factory.
        
        Raises:
            ValueError: if the credentials are not valid.

        """
        credentials_valid = _validate_credentials(**credentials)
        if not credentials_valid:
            raise ValueError(
                "Given private key doesn't match the ethereum address.")

        self.ipfs_client = ipfs_client
        if not ipfs_client:
            self.ipfs_client = connect(IPFS_HOST, IPFS_PORT)

        self.gas_payer = Web3.toChecksumAddress(credentials["gas_payer"])
        self.gas_payer_priv = credentials["gas_payer_priv"]

        if escrow_addr and factory_addr:
            if not _factory_contains_escrow(factory_addr, escrow_addr,
                                            self.gas_payer):
                raise ValueError(
                    "Given factory address doesn't contain the given escrow address."
                )
            self._access_job(factory_addr, escrow_addr, **credentials)
        else:
            self.factory_contract = _init_factory(factory_addr, credentials)
            self._init_job(escrow_manifest)

    def _manifest_url(self, gas: int = GAS_LIMIT) -> str:
        """Retrieves the deployd manifest url uploaded on Job initialization.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> job._manifest_url() == job.manifest_url
        True

        Args:
            escrow_contract (Contract): the contract to be read.
            gas_payer (str): an ethereum address paying for the gas costs.
            gas (int): maximum amount of gas the caller is ready to pay.
        
        Returns:
            str: returns the manifest url of Job's escrow contract.

        """
        return self.job_contract.functions.getManifestUrl().call({
            'from':
            self.gas_payer,
            'gas':
            gas
        })

    def _manifest_hash(self, gas: int = GAS_LIMIT) -> str:
        """Retrieves the deployd manifest hash uploaded on Job initialization.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> job._manifest_hash() == job.manifest_hash
        True

        Args:
            escrow_contract (Contract): the contract to be read.
            gas_payer (str): an ethereum address paying for the gas costs.
            gas (int): maximum amount of gas the caller is ready to pay.
        
        Returns:
            str: returns the manifest hash of Job's escrow contract.

        """
        return self.job_contract.functions.getManifestHash().call({
            'from':
            self.gas_payer,
            'gas':
            gas
        })

    def _access_job(self, factory_addr: str, escrow_addr: str, **credentials):
        """Given a factory and escrow address and credentials, access an already
        launched manifest of an already deployed escrow contract.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job.launch(rep_oracle_pub_key)
        True
        
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        ...     "rep_oracle_priv_key": b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> escrow_addr = job.job_contract.address
        >>> factory_addr = job.factory_contract.address

        Args:
            factory_addr (str): an ethereum address of the escrow factory contract.
            escrow_addr (str): an ethereum address of the escrow contract.
            **credentials: an unpacked dict of an ethereum address and its private key.

        """
        rep_oracle_priv_key = credentials["rep_oracle_priv_key"]

        self.factory_contract = get_factory(factory_addr)
        self.job_contract = get_escrow(escrow_addr)
        self.manifest_hash = self._manifest_hash()
        self.manifest_url = self._manifest_url()
        manifest_dict = self.manifest(rep_oracle_priv_key)
        escrow_manifest = Manifest(manifest_dict)
        self._init_job(escrow_manifest)

    def _init_job(self, manifest: Manifest):
        """Initialize a Job's class attributes with a given manifest.

        Args:
            manifest (Manifest): a dict representation of the Manifest model.
        
        """
        serialized_manifest = dict(manifest.serialize())
        per_job_cost = Decimal(serialized_manifest['task_bid_price'])
        number_of_answers = int(serialized_manifest['job_total_tasks'])
        self.serialized_manifest = serialized_manifest
        self.amount = Decimal(per_job_cost * number_of_answers)

    def launch(self, pub_key: bytes) -> bool:
        """Launches an escrow contract to the network, uploads the manifest
        to IPFS with the public key of the Reputation Oracle and stores 
        the IPFS url to the escrow contract.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)

        Deploying a new Job to the ethereum network succeeds.
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.status()
        <Status.Launched: 1>

        Args:
            pub_key (bytes): the public key of the Reputation Oracle.

        Returns:
            bool: returns True if Job initialization and Ethereum and IPFS transactions succeed.

        """
        if hasattr(self, "job_contract"):
            raise AttributeError("The escrow has been already deployed.")

        # Use factory to deploy a new escrow contract.
        _create_escrow(self)
        job_addr = _last_escrow_addr(self)
        LOG.info("Job's escrow contract deployed to:{}".format(job_addr))
        self.job_contract = get_escrow(job_addr)

        # Upload the manifest to IPFS.
        (hash_, manifest_url) = upload(self.ipfs_client,
                                       self.serialized_manifest, pub_key)
        self.manifest_url = manifest_url
        self.manifest_hash = hash_
        return self.status() == Status.Launched and _balance(self) == 0

    def setup(self, gas: int = GAS_LIMIT) -> bool:
        """Sets the escrow contract to be ready to receive answers from the Recording Oracle.
        The contract needs to be deployed and funded first.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)

        A Job can't be setup without deploying it first.
        >>> job.setup()
        Traceback (most recent call last):
        AttributeError: 'Job' object has no attribute 'job_contract'

        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True

        Returns:
            bool: returns True if Job is in Pending state.
        
        Raises:
            AttributeError: if trying to setup the job before deploying it.

        """
        # Prepare setup arguments for the escrow contract.
        reputation_oracle_stake = int(
            Decimal(self.serialized_manifest["oracle_stake"]) * 100)
        recording_oracle_stake = int(
            Decimal(self.serialized_manifest["oracle_stake"]) * 100)
        reputation_oracle = str(
            self.serialized_manifest["reputation_oracle_addr"])
        recording_oracle = str(
            self.serialized_manifest["recording_oracle_addr"])
        hmt_amount = int(self.amount * 10**18)

        # Fund the escrow contract with HMT.
        hmtoken_contract = get_hmtoken()
        txn_func = hmtoken_contract.functions.transfer
        func_args = [self.job_contract.address, hmt_amount]
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas
        }
        handle_transaction(txn_func, *func_args, **txn_info)

        # Setup the escrow contract with manifest and IPFS data.
        txn_func = self.job_contract.functions.setup
        func_args = [
            reputation_oracle, recording_oracle, reputation_oracle_stake,
            recording_oracle_stake, self.manifest_url, self.manifest_hash
        ]
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas
        }
        handle_transaction(txn_func, *func_args, **txn_info)
        return self.status() == Status.Pending and _balance(self) == hmt_amount

    def bulk_payout(self,
                    payouts: List[Tuple[str, Decimal]],
                    results: Dict,
                    pub_key: bytes,
                    gas: int = GAS_LIMIT) -> bool:
        """Performs a payout to multiple ethereum addresses. When the payout happens,
        final results are uploaded to IPFS and contract's state is updated to Partial or Paid
        depending on contract's balance.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
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

        Paying the remaining amount empties the escrow and updates the status correctly.
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
            pub_key (bytes): the public key of the Reputation Oracle.

        Returns:
            bool: returns True if paying to ethereum addresses and oracles succeeds.

        """
        (hash_, url) = upload(self.ipfs_client, results, pub_key)
        eth_addrs = [eth_addr for eth_addr, amount in payouts]
        hmt_amounts = [int(amount * 10**18) for eth_addr, amount in payouts]

        txn_func = self.job_contract.functions.bulkPayOut
        func_args = [eth_addrs, hmt_amounts, url, hash_, 1]
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas
        }

        handle_transaction(txn_func, *func_args, **txn_info)
        return _bulk_paid(self) == True

    def abort(self, gas: int = GAS_LIMIT) -> bool:
        """Kills the contract and returns the HMT back to the gas payer.
        The contract cannot be aborted if the contract is in Partial, Paid or Complete state.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)

        The escrow contract is in Pending state after setup so it can be aborted.
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> job.abort()
        True

        The escrow contract is in Partial state after the first payout and it can't be aborted.
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
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
        txn_func = self.job_contract.functions.abort
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas
        }

        handle_transaction(txn_func, *[], **txn_info)

        # After abort the contract should be destroyed
        w3 = get_w3()
        contract_code = w3.eth.getCode(self.job_contract.address)
        return contract_code == b"\x00"

    def cancel(self, gas: int = GAS_LIMIT) -> bool:
        """Returns the HMT back to the gas payer. It's the softer version of abort as the contract is not destroyed.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)

        The escrow contract is in Pending state after setup so it can be cancelled.
        >>> job.launch(rep_oracle_pub_key)
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
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
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
        txn_func = self.job_contract.functions.cancel
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas
        }

        handle_transaction(txn_func, *[], **txn_info)
        return self.status(gas) == Status.Cancelled

    def store_intermediate_results(self,
                                   results: Dict,
                                   pub_key: bytes,
                                   gas: int = GAS_LIMIT) -> bool:
        """Recording Oracle stores intermediate results with Reputation Oracle's public key to IPFS
        and updates the contract's state.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True

        Storing intermediate results uploads and updates results url correctly.
        >>> results = {"results": True}
        >>> job.store_intermediate_results(results, rep_oracle_pub_key)
        True
        >>> rep_oracle_priv_key = b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> job.intermediate_results(rep_oracle_priv_key)
        {'results': True}

        Args:
            results (Dict): intermediate results of the Recording Oracle.
            pub_key (bytes): public key of the Reputation Oracle.
        
        Returns:
            returns True if contract's state is updated and IPFS upload succeeds.

        """
        (hash_, url) = upload(self.ipfs_client, results, pub_key)
        txn_func = self.job_contract.functions.storeResults
        func_args = [url, hash_]
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas
        }

        handle_transaction(txn_func, *func_args, **txn_info)
        return True

    def status(self, gas: int = GAS_LIMIT) -> Enum:
        """Returns the status of the Job.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        
        After deployment status is "Launched".
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.status()
        <Status.Launched: 1>

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

    def complete(self, gas: int = GAS_LIMIT) -> bool:
        """Completes the Job if it has been paid.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True

        A Job can't be completed when it is still in partially paid state.
        >>> job.status()
        <Status.Partial: 3>
        >>> job.complete()
        False

        Job completes in paid state correctly.
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('80.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True
        >>> job.complete()
        True
        >>> job.status()
        <Status.Complete: 5>

        Returns:
            bool: returns True if the contract has been completed.
            
        """
        txn_func = self.job_contract.functions.complete
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas
        }

        handle_transaction(txn_func, *[], **txn_info)
        return self.status() == Status.Complete

    @timeout_decorator.timeout(20)
    def manifest(self, priv_key: bytes) -> Dict:
        """Retrieves the initial manifest used to setup a Job.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> rep_oracle_priv_key = b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> manifest = job.manifest(rep_oracle_priv_key)
        >>> manifest_amount = int(int(manifest["job_total_tasks"]) * Decimal(manifest["task_bid_price"]))
        >>> manifest_amount == job.amount
        True

        Args:
            priv_key (bytes): the private key used to download the manifest.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        key = self.manifest_url
        return download(self.ipfs_client, key, priv_key)

    def intermediate_results(self, priv_key: bytes,
                             gas: int = GAS_LIMIT) -> Dict:
        """Reputation Oracle retrieves the intermediate results stored by the Recording Oracle.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True

        Trying to download the results with the wrong key fails.
        >>> results = {"results": True}
        >>> job.store_intermediate_results(results, rep_oracle_pub_key)
        True
        >>> rep_oracle_false_priv_key = b"486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"
        >>> job.intermediate_results(rep_oracle_false_priv_key)
        Traceback (most recent call last):
        p2p.exceptions.DecryptionError: Failed to verify tag

        Args:
            priv_key (bytes): the private key of the Reputation Oracle.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        intermediate_results_url = self.job_contract.functions.getIntermediateResultsUrl(
        ).call({
            'from': self.gas_payer,
            'gas': gas
        })
        return download(self.ipfs_client, intermediate_results_url, priv_key)

    def final_results(self, priv_key: bytes, gas: int = GAS_LIMIT) -> Dict:
        """Retrieves the final results stored by the Reputation Oracle.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True

        Getting final results succeeds after payout.
        >>> payouts = [("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('100.0'))]
        >>> job.bulk_payout(payouts, {'results': 0}, rep_oracle_pub_key)
        True
        >>> rep_oracle_priv_key = "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        >>> job.final_results(rep_oracle_priv_key)
        {'results': 0}

        Args:
            priv_key (bytes): the private key of the the job requester or their agent.

        Returns:
            bool: returns True if IPFS download with the private key succeeds.

        """
        final_results_url = self.job_contract.functions.getFinalResultsUrl(
        ).call({
            'from': self.gas_payer,
            'gas': gas
        })
        return download(self.ipfs_client, final_results_url, priv_key)


def _validate_credentials(**credentials) -> bool:
    """Validates whether the given ethereum private key maps to the address
    by calculating the checksum address from the private key and comparing that
    to the given address.

    Validating right credentials succeeds.
    >>> credentials = {
    ...     "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> _validate_credentials(**credentials)
    True

    Validating falsy credentials fails.
    >>> credentials = {
    ...     "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"
    ... }
    >>> _validate_credentials(**credentials)
    False

    Args:
        **credentials: an unpacked dict of an ethereum address and its private key.
    
    Returns:
        bool: returns True if the calculated and the given address match.

    """
    addr = credentials["gas_payer"]
    priv_key = credentials["gas_payer_priv"]

    priv_key_bytes = decode_hex(priv_key)
    pub_key = keys.PrivateKey(priv_key_bytes).public_key
    calculated_addr = pub_key.to_checksum_address()
    return Web3.toChecksumAddress(addr) == calculated_addr


def _factory_contains_escrow(factory_addr: str,
                             escrow_addr: str,
                             gas_payer: str,
                             gas: int = GAS_LIMIT) -> bool:
    """Checks whether a given factory address contains a given escrow address.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
    >>> job.launch(rep_oracle_pub_key)
    True
    >>> job.setup()
    True

    Factory contains the escrow address.
    >>> factory_addr = job.factory_contract.address
    >>> escrow_addr = job.job_contract.address
    >>> _factory_contains_escrow(factory_addr, escrow_addr, job.gas_payer)
    True
    
    Args:
        factory_addr (str): an ethereum address of the escrow factory contract.
        escrow_addr (str): an ethereum address of the escrow contract.
        gas_payer (str): an ethereum address calling the contract.
        gas (int): maximum amount of gas the caller is ready to pay.

    Returns:
        bool: returns True escrow belongs to the factory.

    """
    factory_contract = get_factory(factory_addr)
    return factory_contract.functions.hasEscrow(escrow_addr).call({
        'from':
        gas_payer,
        'gas':
        gas
    })


def _init_factory(factory_addr: Optional[str],
                  credentials: Dict[str, str],
                  gas: int = GAS_LIMIT) -> Contract:
    """Takes an optional factory address and returns its contract representation. Alternatively
    a new factory is created.

    Initializing a new Job instance without a factory address succeeds.
    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
    >>> type(job.factory_contract)
    <class 'web3.utils.datatypes.Contract'>

    Initializing a new Job instance with a factory address succeeds.
    >>> factory_addr = deploy_factory(**credentials)
    >>> job = Job(credentials, manifest, factory_addr)
    >>> job.factory_contract.address == factory_addr
    True

    Args:
        credentials (Dict[str, str]): a dict of an ethereum address and its private key.
        factory_addr (Optional[str]): an ethereum address of the escrow factory contract.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns a factory contract.

    """
    factory_addr_valid = Web3.isChecksumAddress(factory_addr)
    factory = None

    if not factory_addr_valid:
        factory_addr = deploy_factory(GAS_LIMIT, **credentials)
        factory = get_factory(factory_addr)
        if not factory_addr:
            raise Exception("Unable to get address from factory")

    if not factory:
        factory = get_factory(factory_addr)
    return factory


def _balance(job: Job, gas: int = GAS_LIMIT) -> int:
    """Retrieve the balance of a Job in HMT.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
    >>> job.launch(rep_oracle_pub_key)
    True
    >>> job.setup()
    True
    >>> _balance(job)
    100000000000000000000

    Args:
        escrow_contract (Contract): the contract to be read.
        gas_payer (str): an ethereum address calling the contract.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        int: returns the balance of the contract in HMT.

    """
    return job.job_contract.functions.getBalance().call({
        'from': job.gas_payer,
        'gas': gas
    })


def _bulk_paid(job: Job, gas: int = GAS_LIMIT) -> int:
    """Checks if the last bulk payment has succeeded.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
    >>> job.launch(rep_oracle_pub_key)
    True
    >>> job.setup()
    True

    No payout has been performed yet.
    >>> _bulk_paid(job)
    False

    Bulk has been paid upon successful bulk payout.
    >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0')), ("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('50.0'))]
    >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
    True
    >>> _bulk_paid(job)
    True

    Args:
        job (Job): class instance of the Job class.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        returns True if the last bulk payout has succeeded.

    """
    escrow_contract = job.job_contract
    gas_payer = job.gas_payer
    return escrow_contract.functions.getBulkPaid().call({
        'from': gas_payer,
        'gas': gas
    })


def _last_escrow_addr(job: Job, gas: int = GAS_LIMIT) -> str:
    """Gets the last deployed escrow contract address of the initialized factory contract.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> factory_addr = deploy_factory(**credentials)
    >>> job = Job(credentials, manifest, factory_addr)
    >>> job.launch(rep_oracle_pub_key)
    True
    >>> _last_escrow_addr(job) == job.job_contract.address
    True

    Args:
        job (Job): class instance of the Job class.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        str: returns an escrow contract address.

    """
    return job.factory_contract.functions.getLastEscrow().call({
        'from':
        job.gas_payer,
        'gas':
        gas
    })


def _create_escrow(job: Job, gas: int = GAS_LIMIT) -> bool:
    """Launches a new escrow contract to the ethereum network.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> job = Job(credentials=credentials, escrow_manifest=manifest, ipfs_client=ipfs_client)
    >>> _create_escrow(job)
    True

    Args:
        job (Job): class instance of the Job class.
        gas (int): maximum amount of gas the caller is ready to pay.
    
    Returns:
        bool: returns True if a new job was successfully launched to the network.
    
    Raises:
        TimeoutError: if wait_on_transaction times out.

    """
    txn_func = job.factory_contract.functions.createEscrow
    txn_info = {
        "gas_payer": job.gas_payer,
        "gas_payer_priv": job.gas_payer_priv,
        "gas": gas
    }

    handle_transaction(txn_func, *[], **txn_info)
    return True


if __name__ == "__main__":
    import doctest
    from test_manifest import manifest
    from test_ipfs import ipfs_client
    from storage import connect
    doctest.testmod()
