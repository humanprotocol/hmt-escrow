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

from hmt_escrow.eth_bridge import get_eip20, get_contract_interface, wait_on_transaction, get_escrow, get_factory, deploy_factory, get_w3, sign_and_send_transaction
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
ESCROW_FACTORY = os.getenv("FACTORYADDR", None)
LOG = logging.getLogger("hmt_escrow")


def _bulk_payout_sol(escrow_contract: Contract,
                     addresses: list,
                     amounts: list,
                     uri: str,
                     hash_: str,
                     gas: int = DEFAULT_GAS):
    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = escrow_contract.functions.bulkPayOut(addresses, amounts, uri,
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

    escrow_contract.functions.storeResults(uri, hash_).call({
        'from': GAS_PAYER,
        'gas': gas
    })
    return True


def _complete(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> bool:
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

    return bool(escrow_contract.functions.complete().call({
        'from': GAS_PAYER,
        'gas': gas
    }))


def _manifest_hash(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> str:
    return escrow_contract.functions.getHash().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _intermediate_manifest_hash(escrow_contract: Contract,
                                gas: int = DEFAULT_GAS) -> str:
    return escrow_contract.functions.getIHash().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _final_manifest_hash(escrow_contract: Contract,
                         gas: int = DEFAULT_GAS) -> str:
    return escrow_contract.functions.getFHash().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _manifest_url(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> str:
    return escrow_contract.functions.getUrl().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _intermediate_manifest_url(escrow_contract: Contract,
                               gas: int = DEFAULT_GAS) -> str:
    return escrow_contract.functions.getIUrl().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _final_manifest_url(escrow_contract: Contract,
                        gas: int = DEFAULT_GAS) -> str:
    return escrow_contract.functions.getFUrl().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _balance(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> int:
    return escrow_contract.functions.getBalance().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _status(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> int:
    return escrow_contract.functions.getStatus().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _abort_sol(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> bool:
    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = escrow_contract.functions.abort().buildTransaction({
        'from': GAS_PAYER,
        'gas': gas,
        'nonce': nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)

    return escrow_contract.functions.getStatus().call({
        'from': GAS_PAYER,
        'gas': gas
    }) == 5  # Cancelled


def _refund_sol(escrow_contract: Contract, gas: int = DEFAULT_GAS) -> bool:
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

    return escrow_contract.functions.getStatus().call({
        'from': GAS_PAYER,
        'gas': gas
    }) == 5  # Cancelled


def _counter(factory_contract: Contract, gas: int = DEFAULT_GAS) -> int:
    return factory_contract.functions.getCounter().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _last_address(factory_contract: Contract, gas: int = DEFAULT_GAS) -> str:
    return factory_contract.functions.getLastAddress().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _create_escrow_sol(factory_contract: Contract,
                       gas: int = DEFAULT_GAS) -> bool:
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


def _setup_sol(escrow: 'Escrow', gas: int = DEFAULT_GAS) -> bool:
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

    return escrow_contract.functions.getStatus().call({
        'from': GAS_PAYER,
        'gas': gas
    }) == 1  # Pending


def _transfer_to_address(address: str, amount: Decimal,
                         gas: int = DEFAULT_GAS) -> bool:
    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)
    eip20_contract = get_eip20()

    tx_dict = eip20_contract.functions.transfer(address,
                                                amount).buildTransaction({
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


class Escrow(Manifest):
    initialized = False

    def initialize(self, manifest: Dict) -> bool:
        if self.initialized:
            raise Exception("Unable to reinitialize if we already have")
        self.per_job_cost = Decimal(manifest['task_bid_price'])
        self.oracle_stake = Decimal(manifest['oracle_stake'])
        self.recording_oracle = manifest['recording_oracle_addr']
        self.reputation_oracle = manifest['reputation_oracle_addr']
        self.number_of_answers = int(manifest['job_total_tasks'])
        self.oracle_stake = Decimal(manifest['oracle_stake'])
        self.amount = Decimal(self.per_job_cost * self.number_of_answers)
        self.initialized = True
        return True

    def deploy(self, public_key: bytes, private_key: bytes) -> bool:
        """
        Deploy the contract to the blockchain for funding and activation
        :param public_key:  The public key to encrypt the manifest for
        :param private_key:  The private key to encrypt the manifest
        """
        job_address = get_job()
        self.job_contract = get_job_from_address(job_address)
        serialized_manifest = self.serialize()
        self.initialize(serialized_manifest)
        (hash_, manifest_url) = upload(serialized_manifest, public_key)
        self.manifest_url = manifest_url
        self.manifest_hash = hash_
        return True

    def fund(self) -> bool:
        """
        Actually transfer ether to the contract.
        """
        return _transfer_to_address(self.job_contract.address, self.amount)

    def refund(self) -> bool:
        """
        Transfer ether back to the contract initiator.
        """
        return _refund_sol(self.job_contract)

    def abort(self) -> bool:
        """
        Transfer back the money to the funder of the contract
        """
        return _abort_sol(self.job_contract)

    def launch(self) -> bool:
        """
        Actually launch the ethereum contract to the blockchain

        :return: Returns if the job is pending
        """
        return setup_job(self)

    def status(self) -> Enum:
        """
        Return the status of a contract
        :return:  Returns the status as a fancy enumeration
        """
        return status(self.job_contract)

    def store_intermediate(self, results: Dict, public_key: bytes,
                           private_key: bytes) -> bool:
        (hash_, url) = upload(results, public_key)
        return store_results(self.job_contract, url, hash_)

    def bulk_payout(self, payouts: List[Tuple[str, int]], results: Dict,
                    public_key: bytes, private_key: bytes) -> bool:
        '''
        Takes in a matching list of addresses and amounts to pay, as well
        as a dict of the final results. Uploads final results to IPFS,
        and stores that URI + hash to the escrow contract upon payout.
        
        Returns Undefined (XXX: @rbval) if successful.
        '''
        (hash_, url) = upload(results, public_key)

        eth_addrs = [eth_addr for eth_addr, amount in payouts]
        # Convert amounts to HMT
        hmt_amounts = [int(amount * 10**18) for eth_addr, amount in payouts]

        return _bulk_payout_sol(self.job_contract, eth_addrs, hmt_amounts, url,
                                hash_)

    def complete(self) -> bool:
        try:
            return _complete(self.job_contract)
        except Exception as e:
            LOG.error("Unable to complete contract:{} is the exception".format(
                str(e)))
            return False

    def get_manifest(self, private_key: bytes) -> Dict:
        return download(_manifest_url(self.job_contract), private_key)

    def get_intermediate_results(self, private_key: bytes) -> Dict:
        return download(
            _intermediate_manifest_url(self.job_contract), private_key)

    def get_results(self, private_key: bytes) -> Dict:
        return download(_final_manifest_url(self.job_contract), private_key)


def access_job(escrow_address: str, private_key: bytes) -> Contract:
    job = get_job_from_address(escrow_address)
    url = _manifest_url(job)
    manifest_dict = download(url, private_key)
    contract_manifest = Manifest(manifest_dict)
    contract = Contract(contract_manifest)
    contract.serialize(contract)
    return contract


def get_job() -> str:
    """ Get a new job and launch it without funds on the blockchain.

        This is the first step of putting a new job on the blockchain.
        After this function is called the user can add funds, abort, or set the job up for pending.

        Args:
            gas (int): How much gas to get on the contract.
        Returns:
            Contract: The contract launched on the blockchain
            """

    factory = None
    if not ESCROW_FACTORY:
        factory = deploy_factory()
        ESCROW_FACTORY = factory.address
        if not ESCROW_FACTORY:
            raise Exception("Unable to get address from factory")

    if factory is None:
        factory = get_factory(ESCROW_FACTORY)
        counter = _counter(factory)
        LOG.debug("Factory counter is at:{}".format(counter))

    _create_escrow_sol(factory)
    escrow_address = _last_address(factory)

    LOG.info("New pokemon!:{}".format(escrow_address))
    return escrow_address


def get_job_from_address(escrow_address: str) -> Contract:
    return get_escrow(escrow_address)


def setup_job(escrow: Escrow) -> bool:
    """ Once a job is started we can start a job to be processing.


        Once a job hash been put on blockchain, and is funded, this function will
        setup the job for labeling (Pending):

        Args:
            contract (Contract): The actual ethereum contract instantiated.
            amount (int): The amount of token that the job represents.
            manifest_url (str): The url to the questions to be answered.
            manifest_hash: The hash of the plaintext of the manifest.

        Returns:
            bool: True if the contract is pending """

    return _setup_sol(escrow)


def abort_job(escrow_contract: Contract) -> bool:
    """ Return all leftover funds to the contract launcher

        Once a job hash been put on blockchain, and is funded, this function can return
        the money to the funder of the contract. This function cannot run if the contract has
        already been partially paid.

        Args:
            contract (Contract): The actual ethereum contract instantiated.
            gas (int): The amount of gas to run the transaction with.
        Returns:
            bool: True if the contract is pending """
    return _abort_sol(escrow_contract)


def store_results(escrow_contract: Contract, manifest_url: str,
                  manifest_hash: str) -> bool:
    """ Store intermediate results in the contract

        Store intermediate manifest results

        Args:
            contract (Contract): The actual ethereum contract instantiated.
            manifest_url (str): The url of the answers to the questions
            manifest_hash: The hash of the plaintext of the manifest.
            gas (int): The amount of gas to run the transaction with.
        Returns:
            bool: True if the results storage was successful """
    return _store_results(escrow_contract, manifest_url, manifest_hash)


Status = Enum('Status', 'Launched Pending Partial Paid Complete Cancelled')


def status(escrow_contract: Contract) -> Enum:
    """ User friendly status.

    Returns the status of a contract
    From solidity
    enum EscrowStatuses { Launched, Pending, Partial, Paid, Complete, Cancelled }

    Args:
        contract (Contract): The actual ethereum contract instantiated.
        gas (int): The amount of gas to run the transaction with.
    Returns:
        Status: The enum which represents the state.
    """
    status_ = _status(escrow_contract)
    return Status(status_ + 1)
