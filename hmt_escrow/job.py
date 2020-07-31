#!/usr/bin/env python3
import os
import sys
import logging
import unittest

from decimal import Decimal
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any

from web3 import Web3
from web3.contract import Contract
from web3.types import Wei
from eth_keys import keys
from eth_utils import decode_hex

from hmt_escrow.eth_bridge import (
    get_hmtoken,
    get_contract_interface,
    get_escrow,
    get_factory,
    deploy_factory,
    get_w3,
    handle_transaction,
)
from hmt_escrow.storage import download, upload
from basemodels import Manifest

GAS_LIMIT = int(os.getenv("GAS_LIMIT", 4712388))

# Explicit env variable that will use s3 for storing results.

LOG = logging.getLogger("hmt_escrow.job")
Status = Enum("Status", "Launched Pending Partial Paid Complete Cancelled")


def status(escrow_contract: Contract, gas_payer: str, gas: int = GAS_LIMIT) -> Enum:
    """Returns the status of the Job.

    >>> from test_manifest import manifest
    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials, manifest)

    After deployment status is "Launched".

    >>> job.launch(rep_oracle_pub_key)
    True
    >>> status(job.job_contract, job.gas_payer)
    <Status.Launched: 1>

    Args:
        escrow_contract (Contract): the escrow contract of the Job.
        gas_payer (str): an ethereum address paying for the gas costs.
        gas (int): maximum amount of gas the caller is ready to pay.

    Returns:
        Enum: returns the status as an enumeration.

    """
    status_ = escrow_contract.functions.getStatus().call(
        {"from": gas_payer, "gas": Wei(gas)}
    )
    return Status(status_ + 1)


def manifest_url(
    escrow_contract: Contract, gas_payer: str, gas: int = GAS_LIMIT
) -> str:
    """Retrieves the deployed manifest url uploaded on Job initialization.

    >>> from test_manifest import manifest
    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> job = Job(credentials, manifest)
    >>> job.launch(rep_oracle_pub_key)
    True
    >>> job.setup()
    True
    >>> manifest_hash(job.job_contract, job.gas_payer) == job.manifest_hash
    True

    Args:
        escrow_contract (Contract): the escrow contract of the Job.
        gas_payer (str): an ethereum address paying for the gas costs.
        gas (int): maximum amount of gas the caller is ready to pay.

    Returns:
        str: returns the manifest url of Job's escrow contract.

    """
    return escrow_contract.functions.getManifestUrl().call(
        {"from": gas_payer, "gas": Wei(gas)}
    )


def manifest_hash(
    escrow_contract: Contract, gas_payer: str, gas: int = GAS_LIMIT
) -> str:
    """Retrieves the deployed manifest hash uploaded on Job initialization.

    >>> credentials = {
    ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
    ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
    ... }
    >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
    >>> from test_manifest import manifest
    >>> job = Job(credentials, manifest)
    >>> job.launch(rep_oracle_pub_key)
    True
    >>> job.setup()
    True
    >>> manifest_hash(job.job_contract, job.gas_payer) == job.manifest_hash
    True

    Args:
        escrow_contract (Contract): the escrow contract of the Job.
        gas_payer (str): an ethereum address paying for the gas costs.
        gas (int): maximum amount of gas the caller is ready to pay.

    Returns:
        str: returns the manifest hash of Job's escrow contract.

    """
    return escrow_contract.functions.getManifestHash().call(
        {"from": gas_payer, "gas": Wei(gas)}
    )


def is_trusted_handler(
    escrow_contract: Contract, handler_addr: str, gas_payer: str, gas: int = GAS_LIMIT
) -> bool:
    return escrow_contract.functions.isTrustedHandler(handler_addr).call(
        {"from": gas_payer, "gas": Wei(gas)}
    )


def launcher(escrow_contract: Contract, gas_payer: str, gas: int = GAS_LIMIT) -> str:
    """Retrieves the details on what eth wallet launched the job

    Args:
        escrow_contract (Contract): the escrow contract of the Job.
        gas_payer (str): an ethereum address paying for the gas costs.
        gas (int): maximum amount of gas the caller is ready to pay.

    Returns:
        str: returns the address of who launched the job.

    """
    return escrow_contract.functions.getLauncher().call(
        {"from": gas_payer, "gas": Wei(gas)}
    )


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

    def __init__(
        self,
        credentials: Dict[str, str],
        escrow_manifest: Manifest = None,
        factory_addr: str = None,
        escrow_addr: str = None,
        multi_credentials: List[Tuple] = [],
    ):
        """Initializes a Job instance with values from a Manifest class and
        checks that the provided credentials are valid. An optional factory
        address is used to initialize the factory of the Job. Alternatively
        a new factory is created if no factory address is provided.

        Creating a new Job instance initializes the critical attributes correctly.
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> from test_manifest import manifest
        >>> job = Job(credentials, manifest)
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
        >>> launcher(job.job_contract, credentials['gas_payer']).lower() == job.factory_contract.address.lower()
        True

        Initializing an existing Job instance with a factory and escrow address succeeds.
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        ...     "rep_oracle_priv_key": b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> escrow_addr = job.job_contract.address
        >>> factory_addr = job.factory_contract.address
        >>> manifest_url = job.manifest_url
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
        >>> job = Job(credentials, manifest)
        Traceback (most recent call last):
        ValueError: Given private key doesn't match the ethereum address.

        Args:
            manifest (Manifest): an instance of the Manifest class.
            credentials (Dict[str, str]): an ethereum address and its private key.
            factory_addr (str): an ethereum address of the factory.
            escrow_addr (str): an ethereum address of an existing escrow address.
            multi_credentials (List[Tuple]): a list of tuples with ethereum address, private key pairs.

        Raises:
            ValueError: if the credentials are not valid.

        """
        main_credentials_valid = self._validate_credentials(
            multi_credentials, **credentials
        )
        if not main_credentials_valid:
            raise ValueError("Given private key doesn't match the ethereum address.")

        self.gas_payer = Web3.toChecksumAddress(credentials["gas_payer"])
        self.gas_payer_priv = credentials["gas_payer_priv"]
        self.multi_credentials = self._validate_multi_credentials(multi_credentials)

        # Initialize a new Job.
        if not escrow_addr and escrow_manifest:
            self.factory_contract = self._init_factory(factory_addr, credentials)
            self._init_job(escrow_manifest)

        # Access an existing Job.
        elif escrow_addr and factory_addr and not escrow_manifest:
            if not self._factory_contains_escrow(escrow_addr, factory_addr):
                raise ValueError(
                    "Given factory address doesn't contain the given escrow address."
                )
            self._access_job(factory_addr, escrow_addr, **credentials)

        # Handle incorrect usage
        else:
            raise ValueError("Job instantiation wrong, double-check arguments.")

    def launch(self, pub_key: bytes) -> bool:
        """Launches an escrow contract to the network, uploads the manifest
        to S3 with the public key of the Reputation Oracle and stores
        the S3 url to the escrow contract.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)

        Deploying a new Job to the ethereum network succeeds.

        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.status()
        <Status.Launched: 1>

        >>> multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> job = Job(credentials, manifest, multi_credentials=multi_credentials)

        Inject wrong credentials on purpose to test out raffling

        >>> job.gas_payer_priv = "657b6497a355a3982928d5515d48a84870f057c4d16923eb1d104c0afada9aa8"
        >>> job.multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.status()
        <Status.Launched: 1>

        Make sure we launched with raffled credentials

        >>> job.gas_payer
        '0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809'
        >>> job.gas_payer_priv
        'f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1'

        Args:
            pub_key (bytes): the public key of the Reputation Oracle.
        Returns:
            bool: returns True if Job initialization and Ethereum and IPFS transactions succeed.

        """
        if hasattr(self, "job_contract"):
            raise AttributeError("The escrow has been already deployed.")

        # Use factory to deploy a new escrow contract.
        trusted_handlers = [addr for addr, priv_key in self.multi_credentials]
        self._create_escrow(trusted_handlers)
        job_addr = self._last_escrow_addr()
        LOG.info("Job's escrow contract deployed to:{}".format(job_addr))
        self.job_contract = get_escrow(job_addr)

        (hash_, manifest_url) = upload(self.serialized_manifest, pub_key)
        self.manifest_url = manifest_url
        self.manifest_hash = hash_
        return self.status() == Status.Launched and self.balance() == 0

    def setup(self, gas: int = GAS_LIMIT) -> bool:
        """Sets the escrow contract to be ready to receive answers from the Recording Oracle.
        The contract needs to be deployed and funded first.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)

        A Job can't be setup without deploying it first.

        >>> job.setup()
        False

        >>> multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> job = Job(credentials, manifest, multi_credentials=multi_credentials)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.gas_payer_priv = "657b6497a355a3982928d5515d48a84870f057c4d16923eb1d104c0afada9aa8"
        >>> job.multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> job.setup()
        True

        Returns:
            bool: returns True if Job is in Pending state.

        Raises:
            AttributeError: if trying to setup the job before deploying it.

        """

        if not hasattr(self, "job_contract"):
            return False

        # Prepare setup arguments for the escrow contract.
        reputation_oracle_stake = int(
            Decimal(self.serialized_manifest["oracle_stake"]) * 100
        )
        recording_oracle_stake = int(
            Decimal(self.serialized_manifest["oracle_stake"]) * 100
        )
        reputation_oracle = str(self.serialized_manifest["reputation_oracle_addr"])
        recording_oracle = str(self.serialized_manifest["recording_oracle_addr"])
        hmt_amount = int(self.amount * 10 ** 18)
        hmtoken_contract = get_hmtoken()

        hmt_transferred = False
        contract_is_setup = False

        txn_event = "Transferring HMT"
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas,
        }
        txn_func = hmtoken_contract.functions.transfer
        func_args = [self.job_contract.address, hmt_amount]

        try:
            handle_transaction(txn_func, *func_args, **txn_info)
            hmt_transferred = True
        except Exception as e:
            LOG.info(
                f"{txn_event} failed with main credentials: {self.gas_payer}, {self.gas_payer_priv} due to {e}. Using secondary ones..."
            )

        if not hmt_transferred:
            hmt_transferred = self._raffle_txn(
                self.multi_credentials, txn_func, func_args, txn_event
            )

        if not hmt_transferred:
            LOG.exception(
                f"{txn_event} failed with all credentials, not continuing to setup."
            )
            return False

        txn_event = "Setup"
        txn_func = self.job_contract.functions.setup
        func_args = [
            reputation_oracle,
            recording_oracle,
            reputation_oracle_stake,
            recording_oracle_stake,
            self.manifest_url,
            self.manifest_hash,
        ]

        try:
            handle_transaction(txn_func, *func_args, **txn_info)
            contract_is_setup = True
        except Exception as e:
            LOG.info(
                f"{txn_event} failed with main credentials: {self.gas_payer}, {self.gas_payer_priv} due to {e}. Using secondary ones..."
            )

        if not contract_is_setup:
            contract_is_setup = self._raffle_txn(
                self.multi_credentials, txn_func, func_args, txn_event
            )

        if not contract_is_setup:
            LOG.exception(f"{txn_event} failed with all credentials.")

        return self.status() == Status.Pending and self.balance() == hmt_amount

    def add_trusted_handlers(self, handlers: List[str], gas: int = GAS_LIMIT) -> bool:
        """Add trusted handlers that can freely transact with the contract and perform aborts and cancels for example.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
        >>> job.launch(rep_oracle_pub_key)
        True

        Make sure we se set our gas payer as a trusted handler by default.

        >>> is_trusted_handler(job.job_contract, job.gas_payer, job.gas_payer)
        True

        >>> trusted_handlers = ['0x61F9F0B31eacB420553da8BCC59DC617279731Ac', '0xD979105297fB0eee83F7433fC09279cb5B94fFC6']
        >>> job.add_trusted_handlers(trusted_handlers)
        True
        >>> is_trusted_handler(job.job_contract, '0x61F9F0B31eacB420553da8BCC59DC617279731Ac', job.gas_payer)
        True
        >>> is_trusted_handler(job.job_contract, '0xD979105297fB0eee83F7433fC09279cb5B94fFC6', job.gas_payer)
        True

        Args:
            handlers (List[str]): a list of trusted handlers.

        Returns:
            bool: returns True if trusted handlers have been setup successfully.

        """
        txn_event = "Adding trusted handlers"
        txn_func = self.job_contract.functions.addTrustedHandlers
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas,
        }
        func_args = [handlers]

        try:
            handle_transaction(txn_func, *func_args, **txn_info)
            return True
        except Exception as e:
            LOG.info(
                f"{txn_event} failed with main credentials: {self.gas_payer}, {self.gas_payer_priv} due to {e}. Using secondary ones..."
            )
        trusted_handlers_added = self._raffle_txn(
            self.multi_credentials, txn_func, func_args, txn_event
        )

        if not trusted_handlers_added:
            LOG.exception(f"{txn_event} failed with all credentials.")

        return trusted_handlers_added

    def bulk_payout(
        self,
        payouts: List[Tuple[str, Decimal]],
        results: Dict,
        pub_key: bytes,
        gas: int = GAS_LIMIT,
    ) -> bool:
        """Performs a payout to multiple ethereum addresses. When the payout happens,
        final results are uploaded to IPFS and contract's state is updated to Partial or Paid
        depending on contract's balance.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0')), ("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('50.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True

        The escrow contract is still in Partial state as there's still balance left.

        >>> job.balance()
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
        >>> job.balance()
        0
        >>> job.status()
        <Status.Paid: 4>

        >>> multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> job = Job(credentials, manifest, multi_credentials=multi_credentials)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0')), ("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('50.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True

        Args:
            payouts (List[Tuple[str, int]]): a list of tuples with ethereum addresses and amounts.
            results (Dict): the final answer results stored by the Reputation Oracle.
            pub_key (bytes): the public key of the Reputation Oracle.

        Returns:
            bool: returns True if paying to ethereum addresses and oracles succeeds.

        """
        txn_event = "Bulk payout"
        txn_func = self.job_contract.functions.bulkPayOut
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas,
        }

        (hash_, url) = upload(results, pub_key)
        eth_addrs = [eth_addr for eth_addr, amount in payouts]
        hmt_amounts = [int(amount * 10 ** 18) for eth_addr, amount in payouts]

        func_args = [eth_addrs, hmt_amounts, url, hash_, 1]
        try:
            handle_transaction(txn_func, *func_args, **txn_info)
            return self._bulk_paid() == True
        except Exception as e:
            LOG.info(
                f"{txn_event} failed with main credentials: {self.gas_payer}, {self.gas_payer_priv} due to {e}. Using secondary ones..."
            )

        bulk_paid = self._raffle_txn(
            self.multi_credentials, txn_func, func_args, txn_event
        )

        if not bulk_paid:
            LOG.exception(f"{txn_event} failed with all credentials.")

        return bulk_paid == True

    def abort(self, gas: int = GAS_LIMIT) -> bool:
        """Kills the contract and returns the HMT back to the gas payer.
        The contract cannot be aborted if the contract is in Partial, Paid or Complete state.

        Returns:        
            bool: returns True if contract has been destroyed successfully.
        
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"


        The escrow contract is in Partial state after a partial bulk payout so it can be aborted.

        >>> from test_manifest import manifest
        >>> job = Job(credentials, manifest)

        The escrow contract is in Pending state after setup so it can be aborted.

        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True
        >>> job.abort()
        True

        The escrow contract is in Partial state after the first payout and it can't be aborted.


        The escrow contract is in Paid state after the a full bulk payout and it can't be aborted.

        >>> job = Job(credentials, manifest)
        >>> job.launch(rep_oracle_pub_key)
        True

        >>> job.setup()
        True
        >>> payouts = [("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('100.0'))]
        >>> job.bulk_payout(payouts, {'results': 0}, rep_oracle_pub_key)
        True
        >>> job.abort()
        False
        >>> job.status()
        <Status.Paid: 4>


        Trusted handler should be able to abort an existing contract

        >>> trusted_handler = "0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809"
        >>> job = Job(credentials, manifest)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> job.add_trusted_handlers([trusted_handler])
        True

        >>> handler_credentials = {
        ... 	"gas_payer": "0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809",
        ... 	"gas_payer_priv": "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1",
        ...     "rep_oracle_priv_key": b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> access_job = Job(credentials=handler_credentials, factory_addr=job.factory_contract.address, escrow_addr=job.job_contract.address)
        >>> access_job.abort()
        True

        Returns:
            bool: returns True if contract has been destroyed successfully.

        """
        w3 = get_w3()
        txn_event = "Job abortion"
        txn_func = self.job_contract.functions.abort
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas,
        }

        try:
            handle_transaction(txn_func, *[], **txn_info)
            # After abort the contract should be destroyed
            return w3.eth.getCode(self.job_contract.address) == b""
        except Exception as e:
            LOG.info(
                f"{txn_event} failed with main credentials: {self.gas_payer}, {self.gas_payer_priv} due to {e}. Using secondary ones..."
            )

        job_aborted = self._raffle_txn(self.multi_credentials, txn_func, [], txn_event)

        if not job_aborted:
            LOG.exception(f"{txn_event} failed with all credentials.")

        return w3.eth.getCode(self.job_contract.address) == b""

    def cancel(self, gas: int = GAS_LIMIT) -> bool:
        """Returns the HMT back to the gas payer. It's the softer version of abort as the contract is not destroyed.

        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> from test_manifest import manifest
        >>> job = Job(credentials, manifest)

        The escrow contract is in Pending state after setup so it can be cancelled.

        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> job.cancel()
        True

        Contract balance is zero and status is "Cancelled".

        >>> job.balance()
        0
        >>> job.status()
        <Status.Cancelled: 6>

        The escrow contract is in Partial state after the first payout and it can't be cancelled.

        >>> job = Job(credentials, manifest)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True
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
        txn_event = "Job cancellation"
        txn_func = self.job_contract.functions.cancel
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas,
        }

        try:
            handle_transaction(txn_func, *[], **txn_info)
            return self.status() == Status.Cancelled
        except Exception as e:
            LOG.info(
                f"{txn_event} failed with main credentials: {self.gas_payer}, {self.gas_payer_priv} due to {e}. Using secondary ones..."
            )

        job_cancelled = self._raffle_txn(
            self.multi_credentials, txn_func, [], txn_event
        )

        if not job_cancelled:
            LOG.exception(f"{txn_event} failed with all credentials.")

        return self.status() == Status.Cancelled

    def store_intermediate_results(
        self, results: Dict, pub_key: bytes, gas: int = GAS_LIMIT
    ) -> bool:
        """Recording Oracle stores intermediate results with Reputation Oracle's public key to S3
        and updates the contract's state.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
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

        >>> multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> job = Job(credentials, manifest, multi_credentials=multi_credentials)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> job.store_intermediate_results(results, rep_oracle_pub_key)
        True

        >>> multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> job = Job(credentials, manifest, multi_credentials=multi_credentials)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> results = {"results": False}

        Inject wrong credentials on purpose to test out raffling

        >>> job.gas_payer_priv = "657b6497a355a3982928d5515d48a84870f057c4d16923eb1d104c0afada9aa8"
        >>> job.multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> job.store_intermediate_results(results, rep_oracle_pub_key)
        True

        Args:
            results (Dict): intermediate results of the Recording Oracle.
            pub_key (bytes): public key of the Reputation Oracle.

        Returns:
            returns True if contract's state is updated and IPFS upload succeeds.

        """
        txn_event = "Storing intermediate results"
        txn_func = self.job_contract.functions.storeResults
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas,
        }
        (hash_, url) = upload(results, pub_key)
        func_args = [url, hash_]

        try:
            handle_transaction(txn_func, *func_args, **txn_info)
            return True
        except Exception as e:
            LOG.info(
                f"{txn_event} failed with main credentials: {self.gas_payer}, {self.gas_payer_priv} due to {e}. Using secondary ones..."
            )

        results_stored = self._raffle_txn(
            self.multi_credentials, txn_func, func_args, txn_event
        )

        if not results_stored:
            LOG.exception(f"{txn_event} failed with all credentials.")
        else:
            self.intermediate_manifest_hash = hash_
            self.intermediate_manifest_url = url

        return results_stored

    def complete(self, gas: int = GAS_LIMIT) -> bool:
        """Completes the Job if it has been paid.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
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
        txn_event = "Job completion"
        txn_func = self.job_contract.functions.complete
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas,
        }

        try:
            handle_transaction(txn_func, *[], **txn_info)
            return self.status() == Status.Complete
        except Exception as e:
            LOG.info(
                f"{txn_event} failed with main credentials: {self.gas_payer}, {self.gas_payer_priv} due to {e}. Using secondary ones..."
            )

        job_completed = self._raffle_txn(
            self.multi_credentials, txn_func, [], txn_event
        )

        if not job_completed:
            LOG.exception(f"{txn_event} failed with all credentials.")

        return self.status() == Status.Complete

    def status(self, gas: int = GAS_LIMIT) -> Enum:
        """Returns the status of the Job.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)

        After deployment status is "Launched".

        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.status()
        <Status.Launched: 1>

        Returns:
            Enum: returns the status as an enumeration.

        """
        return status(self.job_contract, self.gas_payer)

    def balance(self, gas: int = GAS_LIMIT) -> int:
        """Retrieve the balance of a Job in HMT.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True
        >>> job.balance()
        100000000000000000000

        Args:
            escrow_contract (Contract): the contract to be read.
            gas_payer (str): an ethereum address calling the contract.
            gas (int): maximum amount of gas the caller is ready to pay.

        Returns:
            int: returns the balance of the contract in HMT.

        """
        return self.job_contract.functions.getBalance().call(
            {"from": self.gas_payer, "gas": Wei(gas)}
        )

    def manifest(self, priv_key: bytes) -> Dict:
        """Retrieves the initial manifest used to setup a Job.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
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
        return download(self.manifest_url, priv_key)

    def intermediate_results(self, priv_key: bytes, gas: int = GAS_LIMIT) -> Dict:
        """Reputation Oracle retrieves the intermediate results stored by the Recording Oracle.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
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
        return download(self.intermediate_manifest_url, priv_key)

    def final_results(self, priv_key: bytes, gas: int = GAS_LIMIT) -> Dict:
        """Retrieves the final results stored by the Reputation Oracle.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
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
        final_results_url = self.job_contract.functions.getFinalResultsUrl().call(
            {"from": self.gas_payer, "gas": Wei(gas)}
        )
        return download(final_results_url, priv_key)

    def _access_job(self, factory_addr: str, escrow_addr: str, **credentials):
        """Given a factory and escrow address and credentials, access an already
        launched manifest of an already deployed escrow contract.

        Args:
            factory_addr (str): an ethereum address of the escrow factory contract.
            escrow_addr (str): an ethereum address of the escrow contract.
            **credentials: an unpacked dict of an ethereum address and its private key.

        """
        gas_payer = credentials["gas_payer"]
        rep_oracle_priv_key = credentials["rep_oracle_priv_key"]

        self.factory_contract = get_factory(factory_addr)
        self.job_contract = get_escrow(escrow_addr)
        self.manifest_url = manifest_url(self.job_contract, gas_payer)
        self.manifest_hash = manifest_hash(self.job_contract, gas_payer)

        manifest_dict = self.manifest(rep_oracle_priv_key)
        escrow_manifest = Manifest(manifest_dict)
        self._init_job(escrow_manifest)

    def _init_job(self, manifest: Manifest):
        """Initialize a Job's class attributes with a given manifest.

        Args:
            manifest (Manifest): a dict representation of the Manifest model.

        """
        serialized_manifest = dict(manifest.serialize())
        per_job_cost = Decimal(serialized_manifest["task_bid_price"])
        number_of_answers = int(serialized_manifest["job_total_tasks"])
        self.serialized_manifest = serialized_manifest
        self.amount = Decimal(per_job_cost * number_of_answers)

    def _eth_addr_valid(self, addr, priv_key):
        priv_key_bytes = decode_hex(priv_key)
        pub_key = keys.PrivateKey(priv_key_bytes).public_key
        calculated_addr = pub_key.to_checksum_address()
        return Web3.toChecksumAddress(addr) == calculated_addr

    def _validate_multi_credentials(
        self, multi_credentials: List[Tuple]
    ) -> List[Tuple[Any, Any]]:
        """Validates whether the given ethereum private key maps to the address
        by calculating the checksum address from the private key and comparing that
        to the given address.

        >>> from test_manifest import manifest
        >>> credentials = {
        ...     "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> valid_multi_credentials = [("0x1413862C2B7054CDbfdc181B83962CB0FC11fD92", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"), ("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e")]
        >>> job = Job(credentials, manifest, multi_credentials=valid_multi_credentials)
        >>> job.multi_credentials
        [('0x1413862C2B7054CDbfdc181B83962CB0FC11fD92', '28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5'), ('0x61F9F0B31eacB420553da8BCC59DC617279731Ac', '486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e')]

        >>> invalid_multi_credentials = [("0x1413862C2B7054CDbfdc181B83962CB0FC11fD92", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"), ("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5")]
        >>> job = Job(credentials, manifest, multi_credentials=invalid_multi_credentials)
        >>> job.multi_credentials
        [('0x1413862C2B7054CDbfdc181B83962CB0FC11fD92', '28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5')]

        Args:
            multi_credentials (List[Tuple]): a list of tuples with ethereum address, private key pairs.

        Returns:
            List (List[Tuple]): returns a list of tuples with ethereum address, private key pairs that are valid.

        """
        valid_credentials = []
        for gas_payer, gas_payer_priv in multi_credentials:
            credentials_valid = self._eth_addr_valid(gas_payer, gas_payer_priv)
            if not credentials_valid:
                LOG.warn(
                    f"Ethereum address {gas_payer} doesn't match private key {gas_payer_priv}"
                )
                continue
            valid_credentials.append((gas_payer, gas_payer_priv))
        return valid_credentials

    def _validate_credentials(
        self, multi_credentials: List[Tuple], **credentials
    ) -> bool:
        """Validates whether the given ethereum private key maps to the address
        by calculating the checksum address from the private key and comparing that
        to the given address.

        Validating right credentials succeeds.
        >>> from test_manifest import manifest
        >>> credentials = {
        ...     "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> job = Job(credentials, manifest)

        >>> multi_credentials = [("0x1413862C2B7054CDbfdc181B83962CB0FC11fD92", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"), ("0x1413862C2B7054CDbfdc181B83962CB0FC11fD92", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5")]
        >>> job = Job(credentials, manifest, multi_credentials=multi_credentials)

        Validating falsy credentials fails.
        >>> credentials = {
        ...     "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"
        ... }
        >>> job = Job(credentials, manifest)
        Traceback (most recent call last):
        ValueError: Given private key doesn't match the ethereum address.

        Args:
            multi_credentials (List[Tuple]): a list of tuples with ethereum address, private key pairs.
            **credentials: an unpacked dict of an ethereum address and its private key.

        Returns:
            bool: returns True if the calculated and the given address match.

        """
        gas_payer_addr = credentials["gas_payer"]
        gas_payer_priv = credentials["gas_payer_priv"]

        return self._eth_addr_valid(gas_payer_addr, gas_payer_priv)

    def _factory_contains_escrow(
        self, escrow_addr: str, factory_addr: str, gas: int = GAS_LIMIT
    ) -> bool:
        """Checks whether a given factory address contains a given escrow address.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        ...     "rep_oracle_priv_key": b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True

        Factory contains the escrow address.
        >>> factory_addr = job.factory_contract.address
        >>> escrow_addr = job.job_contract.address
        >>> new_job = Job(credentials=credentials, factory_addr=factory_addr, escrow_addr=escrow_addr)
        >>> new_job._factory_contains_escrow(escrow_addr, factory_addr)
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
        return factory_contract.functions.hasEscrow(escrow_addr).call(
            {"from": self.gas_payer, "gas": Wei(gas)}
        )

    def _init_factory(
        self,
        factory_addr: Optional[str],
        credentials: Dict[str, str],
        gas: int = GAS_LIMIT,
    ) -> Contract:
        """Takes an optional factory address and returns its contract representation. Alternatively
        a new factory is created.

        Initializing a new Job instance without a factory address succeeds.
        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> job = Job(credentials, manifest)
        >>> type(job.factory_contract)
        <class 'web3._utils.datatypes.Contract'>

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
            factory = get_factory(str(factory_addr))
        return factory

    def _bulk_paid(self, gas: int = GAS_LIMIT) -> int:
        """Checks if the last bulk payment has succeeded.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> job = Job(credentials, manifest)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job.setup()
        True

        No payout has been performed yet.
        >>> job._bulk_paid()
        False

        Bulk has been paid upon successful bulk payout.
        >>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0')), ("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal('50.0'))]
        >>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
        True
        >>> job._bulk_paid()
        True

        Args:
            gas (int): maximum amount of gas the caller is ready to pay.

        Returns:
            returns True if the last bulk payout has succeeded.

        """
        return self.job_contract.functions.getBulkPaid().call(
            {"from": self.gas_payer, "gas": Wei(gas)}
        )

    def _last_escrow_addr(self, gas: int = GAS_LIMIT) -> str:
        """Gets the last deployed escrow contract address of the initialized factory contract.

        >>> from test_manifest import manifest
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        >>> factory_addr = deploy_factory(**credentials)
        >>> job = Job(credentials, manifest, factory_addr)
        >>> job.launch(rep_oracle_pub_key)
        True
        >>> job._last_escrow_addr() == job.job_contract.address
        True

        Args:
            gas (int): maximum amount of gas the caller is ready to pay.

        Returns:
            str: returns an escrow contract address.

        """
        return self.factory_contract.functions.getLastEscrow().call(
            {"from": self.gas_payer, "gas": Wei(gas)}
        )

    def _create_escrow(self, trusted_handlers=[], gas: int = GAS_LIMIT) -> bool:
        """Launches a new escrow contract to the ethereum network.

        >>> from test_manifest import manifest
        >>> multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> trusted_handlers = [addr for addr, priv_key in multi_credentials]
        >>> credentials = {
        ... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
        ... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        ... }
        >>> job = Job(credentials, manifest)
        >>> job._create_escrow(trusted_handlers)
        True

        >>> job = Job(credentials, manifest, multi_credentials=multi_credentials)

        Inject wrong credentials on purpose to test out raffling
        >>> job.gas_payer_priv = "657b6497a355a3982928d5515d48a84870f057c4d16923eb1d104c0afada9aa8"
        >>> job.multi_credentials = [("0x61F9F0B31eacB420553da8BCC59DC617279731Ac", "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"), ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1")]
        >>> job._create_escrow(trusted_handlers)
        True

        Args:
            gas (int): maximum amount of gas the caller is ready to pay.

        Returns:
            bool: returns True if a new job was successfully launched to the network.

        Raises:
            TimeoutError: if wait_on_transaction times out.

        """
        txn_event = "Contract creation"
        txn_func = self.factory_contract.functions.createEscrow
        txn_info = {
            "gas_payer": self.gas_payer,
            "gas_payer_priv": self.gas_payer_priv,
            "gas": gas,
        }
        func_args = [trusted_handlers]

        try:
            handle_transaction(txn_func, *func_args, **txn_info)
            return True
        except Exception as e:
            LOG.info(
                f"{txn_event} failed with main credentials: {self.gas_payer}, {self.gas_payer_priv} due to {e}. Using secondary ones..."
            )

        escrow_created = self._raffle_txn(
            self.multi_credentials, txn_func, func_args, txn_event
        )

        if not escrow_created:
            LOG.exception(f"{txn_event} failed with all credentials.")

        return escrow_created

    def _raffle_txn(
        self, multi_creds, txn_func, txn_args, txn_event, gas: int = GAS_LIMIT
    ):
        """Takes in multiple credentials, loops through each and performs the given transaction.

        Args:
            credentials (Dict[str, str]): a dict of multiple ethereum addresses and their private keys.
            txn_func: the transaction function to be handled.
            txn_args (List): the arguments the transaction takes.
            txn_event (str): the transaction event that will be performed.
            gas (int): maximum amount of gas the caller is ready to pay.
        
        Returns:
            bool: returns True if the given transaction succeeds.

        """
        txn_succeeded = False

        for gas_payer, gas_payer_priv in multi_creds:
            txn_info = {
                "gas_payer": gas_payer,
                "gas_payer_priv": gas_payer_priv,
                "gas": gas,
            }
            try:
                handle_transaction(txn_func, *txn_args, **txn_info)
                self.gas_payer = gas_payer
                self.gas_payer_priv = gas_payer_priv
                txn_succeeded = True
                break
            except Exception as e:
                LOG.info(
                    f"{txn_event} failed with {gas_payer} and {gas_payer_priv} due to {e}."
                )

        return txn_succeeded


class JobTestCase(unittest.TestCase):
    def setUp(self):
        self.credentials = {
            "gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
            "gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        }
        self.rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
        self.job = Job(self.credentials, manifest)

    def test_status(self):
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertEqual(status(self.job.job_contract, self.job.gas_payer), Status(1))

    def test_manifest_url(self):
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(self.job.setup())
        self.assertEqual(
            manifest_hash(self.job.job_contract, self.job.gas_payer),
            self.job.manifest_hash,
        )

    def test_job_init(self):

        # Creating a new Job instance initializes the critical attributes correctly.
        self.assertEqual(self.job.gas_payer, self.credentials["gas_payer"])
        self.assertEqual(self.job.gas_payer_priv, self.credentials["gas_payer_priv"])
        self.assertEqual(self.job.serialized_manifest["oracle_stake"], "0.05")
        self.assertEqual(self.job.amount, Decimal("100.0"))

        # Initializing a new Job instance with a factory address succeeds.
        factory_addr = deploy_factory(**(self.credentials))
        self.job = Job(self.credentials, manifest, factory_addr)
        self.assertTrue(self.job.factory_contract.address, factory_addr)
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(self.job.setup())
        self.assertTrue(
            launcher(self.job.job_contract, self.credentials["gas_payer"]).lower(),
            self.job.factory_contract.address.lower(),
        )

        # Initializing an existing Job instance with a factory and escrow address succeeds.
        self.credentials[
            "rep_oracle_priv_key"
        ] = b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
        escrow_addr = self.job.job_contract.address
        factory_addr = self.job.factory_contract.address
        manifest_url = self.job.manifest_url
        new_job = Job(
            credentials=self.credentials,
            factory_addr=factory_addr,
            escrow_addr=escrow_addr,
        )
        self.assertEqual(new_job.manifest_url, manifest_url)
        self.assertEqual(new_job.job_contract.address, escrow_addr)
        self.assertEqual(new_job.factory_contract.address, factory_addr)
        with self.assertRaises(AttributeError):
            new_job.launch(self.rep_oracle_pub_key)

    def test_job_launch(self):
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertEqual(self.job.status(), Status(1))
        multi_credentials = [
            (
                "0x61F9F0B31eacB420553da8BCC59DC617279731Ac",
                "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e",
            ),
            (
                "0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809",
                "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1",
            ),
        ]
        self.job = Job(self.credentials, manifest, multi_credentials=multi_credentials)

        # Inject wrong credentials on purpose to test out raffling

        self.job.gas_payer_priv = (
            "657b6497a355a3982928d5515d48a84870f057c4d16923eb1d104c0afada9aa8"
        )
        self.job.multi_credentials = [
            (
                "0x61F9F0B31eacB420553da8BCC59DC617279731Ac",
                "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
            ),
            (
                "0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809",
                "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1",
            ),
        ]
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertEqual(self.job.status(), Status(1))

        # Make sure we launched with raffled credentials

        self.assertEqual(
            self.job.gas_payer, "0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809"
        )
        self.assertEqual(
            self.job.gas_payer_priv,
            "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1",
        )

    def test_job_setup(self):

        # A Job can't be setup without deploying it first.

        self.assertFalse(self.job.setup())
        multi_credentials = [
            (
                "0x61F9F0B31eacB420553da8BCC59DC617279731Ac",
                "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
            ),
            (
                "0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809",
                "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1",
            ),
        ]
        self.job = Job(self.credentials, manifest, multi_credentials=multi_credentials)
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(self.job.setup())

    def test_job_add_trusted_handlers(self):

        # Make sure we se set our gas payer as a trusted handler by default.

        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(
            is_trusted_handler(
                self.job.job_contract, self.job.gas_payer, self.job.gas_payer
            )
        )
        trusted_handlers = [
            "0x61F9F0B31eacB420553da8BCC59DC617279731Ac",
            "0xD979105297fB0eee83F7433fC09279cb5B94fFC6",
        ]
        self.assertTrue(self.job.add_trusted_handlers(trusted_handlers))
        self.assertTrue(
            is_trusted_handler(
                self.job.job_contract,
                "0x61F9F0B31eacB420553da8BCC59DC617279731Ac",
                self.job.gas_payer,
            )
        )
        self.assertTrue(
            is_trusted_handler(
                self.job.job_contract,
                "0xD979105297fB0eee83F7433fC09279cb5B94fFC6",
                self.job.gas_payer,
            )
        )

    def test_job_bulk_payout(self):
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(self.job.setup())
        payouts = [
            ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal("20.0")),
            ("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal("50.0")),
        ]
        self.assertTrue(self.job.bulk_payout(payouts, {}, self.rep_oracle_pub_key))

        # The escrow contract is still in Partial state as there's still balance left.

        self.assertEqual(self.job.balance(), 30000000000000000000)
        self.assertEqual(self.job.status(), Status(3))

        # Trying to pay more than the contract balance results in failure.

        payouts = [("0x9d689b8f50Fd2CAec716Cc5220bEd66E03F07B5f", Decimal("40.0"))]
        self.assertFalse(self.job.bulk_payout(payouts, {}, self.rep_oracle_pub_key))

        # Paying the remaining amount empties the escrow and updates the status correctly.

        payouts = [("0x9d689b8f50Fd2CAec716Cc5220bEd66E03F07B5f", Decimal("30.0"))]
        self.assertTrue(self.job.bulk_payout(payouts, {}, self.rep_oracle_pub_key))
        self.assertEqual(self.job.balance(), 0)
        self.assertEqual(self.job.status(), Status(4))

        multi_credentials = [
            (
                "0x61F9F0B31eacB420553da8BCC59DC617279731Ac",
                "486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e",
            ),
            (
                "0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809",
                "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1",
            ),
        ]
        self.job = Job(self.credentials, manifest, multi_credentials=multi_credentials)
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(self.job.setup())
        payouts = [
            ("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal("20.0")),
            ("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal("50.0")),
        ]
        self.assertTrue(self.job.bulk_payout(payouts, {}, self.rep_oracle_pub_key))

    def test_job_abort(self):

        # The escrow contract is in Paid state after the a full bulk payout and it can't be aborted.

        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(self.job.setup())
        payouts = [("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal("100.0"))]
        self.assertTrue(
            self.job.bulk_payout(payouts, {"results": 0}, self.rep_oracle_pub_key)
        )
        self.assertFalse(self.job.abort())
        self.assertEqual(self.job.status(), Status(4))

        # Trusted handler should be able to abort an existing contract

        self.job = Job(self.credentials, manifest)
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(self.job.setup())
        trusted_handler = "0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809"
        self.assertTrue(self.job.add_trusted_handlers([trusted_handler]))

        handler_credentials = {
            "gas_payer": "0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809",
            "gas_payer_priv": "f22d4fc42da79aa5ba839998a0a9f2c2c45f5e55ee7f1504e464d2c71ca199e1",
            "rep_oracle_priv_key": b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
        }
        access_job = Job(
            credentials=handler_credentials,
            factory_addr=self.job.factory_contract.address,
            escrow_addr=self.job.job_contract.address,
        )
        self.assertTrue(access_job.abort())

    def test_job_cancel(self):
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(self.job.setup())
        payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal("20.0"))]
        self.assertTrue(self.job.bulk_payout(payouts, {}, self.rep_oracle_pub_key))
        self.assertEqual(self.job.status(), Status(3))

        # The escrow contract is in Paid state after the second payout and it can't be cancelled.

        payouts = [("0x852023fbb19050B8291a335E5A83Ac9701E7B4E6", Decimal("80.0"))]
        self.assertTrue(
            self.job.bulk_payout(payouts, {"results": 0}, self.rep_oracle_pub_key)
        )
        self.assertFalse(self.job.cancel())
        self.assertEqual(self.job.status(), Status(4))

    def test_job_status(self):
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertEqual(self.job.status(), Status(1))

    def test_job_balance(self):
        self.assertTrue(self.job.launch(self.rep_oracle_pub_key))
        self.assertTrue(self.job.setup())
        self.assertEqual(self.job.balance(), 100000000000000000000)


if __name__ == "__main__":
    from test_manifest import manifest

    unittest.main(exit=False)
