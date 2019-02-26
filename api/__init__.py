import json
import logging
import os
import sys

from decimal import *
from web3 import Web3
from web3.contract import Contract
from enum import Enum

# Access basemodels
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.eth_bridge import get_eip20, get_contract_interface, wait_on_transaction, get_escrow, get_factory, deploy_factory, get_w3, sign_and_send_transaction
from basemodels import Manifest
from api.storage import download, upload

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
LOG = logging.getLogger("api")


def _unlock_account_or_raise(account: str) -> None:
    _validate_account_or_raise(account)


def _validate_account_or_raise(account: str) -> str:
    return account


def _bulk_payout_sol(contract: Contract,
                     addresses: list,
                     amounts: list,
                     uri: str,
                     hash_: str,
                     gas=DEFAULT_GAS):
    W3 = get_w3()
    nonce = W3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = contract.functions.bulkPayOut(addresses, amounts, uri, hash_,
                                            1).buildTransaction({
                                                'from': GAS_PAYER,
                                                'gas': gas,
                                                'nonce': nonce
                                            })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)
    return True


def _store_results(contract: Contract, uri: str, hash_: str,
                   gas=DEFAULT_GAS) -> bool:
    W3 = get_w3()
    nonce = W3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = contract.functions.storeResults(uri, hash_).buildTransaction({
        'from':
        GAS_PAYER,
        'gas':
        gas,
        'nonce':
        nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)

    contract.functions.storeResults(uri, hash_).call({
        'from': GAS_PAYER,
        'gas': gas
    })
    return True


def _complete(contract: Contract, gas=DEFAULT_GAS) -> bool:
    W3 = get_w3()
    nonce = W3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = contract.functions.complete().buildTransaction({
        'from': GAS_PAYER,
        'gas': gas,
        'nonce': nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)

    return bool(contract.functions.complete().call({
        'from': GAS_PAYER,
        'gas': gas
    }))


def _manifest(contract: Contract, gas=DEFAULT_GAS) -> str:
    return contract.functions.getUrl().call({'from': GAS_PAYER, 'gas': gas})


def _hash(contract: Contract, gas=DEFAULT_GAS) -> str:
    return contract.functions.getHash().call({'from': GAS_PAYER, 'gas': gas})


def _hashI(contract: Contract, gas=DEFAULT_GAS) -> str:
    return contract.functions.getIHash().call({'from': GAS_PAYER, 'gas': gas})


def _hashF(contract: Contract, gas=DEFAULT_GAS) -> str:
    return contract.functions.getFHash().call({'from': GAS_PAYER, 'gas': gas})


def _getURL(contract: Contract, gas=DEFAULT_GAS) -> str:
    return contract.functions.getUrl().call({'from': GAS_PAYER, 'gas': gas})


def _getIURL(contract: Contract, gas=DEFAULT_GAS) -> str:
    return contract.functions.getIUrl().call({'from': GAS_PAYER, 'gas': gas})


def _getFURL(contract: Contract, gas=DEFAULT_GAS) -> str:
    return contract.functions.getFUrl().call({'from': GAS_PAYER, 'gas': gas})


def _balance(contract: Contract, gas=DEFAULT_GAS) -> int:
    return contract.functions.getBalance().call({
        'from': GAS_PAYER,
        'gas': gas
    })


def _status(contract: Contract, gas=DEFAULT_GAS) -> int:
    return contract.functions.getStatus().call({'from': GAS_PAYER, 'gas': gas})


def _abort_sol(contract: Contract, gas: int) -> bool:
    W3 = get_w3()
    nonce = W3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = contract.functions.abort().buildTransaction({
        'from': GAS_PAYER,
        'gas': gas,
        'nonce': nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)

    return contract.functions.getStatus().call({
        'from': GAS_PAYER,
        'gas': gas
    }) == 5  # Cancelled


def _setup_sol(contract: Contract,
               reputation_oracle: str,
               recording_oracle: str,
               reputation_oracle_stake: int,
               recording_oracle_stake: int,
               amount: int,
               manifest_url: str,
               manifest_hash: str,
               gas=DEFAULT_GAS) -> bool:

    W3 = get_w3()
    nonce = W3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = contract.functions.setup(
        reputation_oracle, recording_oracle, reputation_oracle_stake,
        recording_oracle_stake, amount, manifest_url,
        manifest_hash).buildTransaction({
            'from': GAS_PAYER,
            'gas': gas,
            'nonce': nonce
        })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)

    return contract.functions.getStatus().call({
        'from': GAS_PAYER,
        'gas': gas
    }) == 1  # Pending


def _refund_sol(contract: Contract, gas: int) -> bool:
    W3 = get_w3()
    nonce = W3.eth.getTransactionCount(GAS_PAYER)

    tx_dict = contract.functions.refund().buildTransaction({
        'from': GAS_PAYER,
        'gas': gas,
        'nonce': nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)

    return contract.functions.getStatus().call({
        'from': GAS_PAYER,
        'gas': gas
    }) == 5  # Cancelled


def _transfer_to_address(address: str, amount: Decimal,
                         gas=DEFAULT_GAS) -> bool:
    W3 = get_w3()
    nonce = W3.eth.getTransactionCount(GAS_PAYER)
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

    def initialize(self, job_contract: Contract, amount: Decimal,
                   oracle_stake: Decimal, number_of_answers: int) -> bool:
        if self.initialized:
            raise Exception("Unable to reinitialize if we already are")
        self.job_contract = job_contract
        self.number_of_answers = number_of_answers
        self.amount = amount
        self.oracle_stake = oracle_stake
        self.initialized = True
        return True

    def deploy(self, public_key: bytes, private_key: bytes) -> bool:
        """
        Deploy the contract to the blockchain for funding and activation
        :param public_key:  The public key to encrypt the manifest for
        :param private_key:  The private key to encrypt the manifest
        """
        job_address = get_job()
        job = get_job_from_address(job_address)

        serialized_manifest = self.serialize()
        per_job_cost = Decimal(serialized_manifest['task_bid_price'])
        number_of_answers = int(serialized_manifest['job_total_tasks'])
        oracle_stake = Decimal(serialized_manifest['oracle_stake'])
        amount = Decimal(per_job_cost * number_of_answers)

        self.initialize(job, amount, oracle_stake, number_of_answers)
        (hash_, manifest_url) = upload(serialized_manifest, public_key)

        self.manifest_url = manifest_url
        self.manifest_hash = hash_
        return True

    def fund(self) -> bool:
        """
        Actually transfer ether to the contract.
        """
        return _transfer_to_address(self.job_contract.address, self.amount)

    def refund(self, gas=DEFAULT_GAS) -> bool:
        """
        Transfer ether back to the contract initiator.
        """
        return _refund_sol(self.job_contract, gas)

    def abort(self, gas=DEFAULT_GAS) -> bool:
        """
        Transfer back the money to the funder of the contract
        """
        return _abort_sol(self.job_contract, gas)

    def launch(self) -> bool:
        """
        Actually launch the ethereum contract to the blockchain

        :return: Returns if the job is pending
        """
        return setup_job(self.job_contract, self.amount, self.oracle_stake,
                         self.manifest_url, self.manifest_hash)

    def status(self) -> Enum:
        """
        Return the status of a contract
        :return:  Returns the status as a fancy enumeration
        """
        return status(self.job_contract)

    def store_intermediate(self, results: dict, public_key: bytes,
                           private_key: bytes) -> bool:
        (hash_, url) = upload(results, public_key)
        return store_results(self.job_contract, url, hash_)

    def bulk_payout(self, addresses: list, amounts: list, results: dict,
                    public_key: bytes, private_key: bytes) -> bool:
        '''
        Takes in a matching list of addresses and amounts to pay, as well
        as a dict of the final results. Uploads final results to IPFS,
        and stores that URI + hash to the escrow contract upon payout.
        
        Returns Undefined (XXX: @rbval) if successful.
        '''
        (hash_, url) = upload(results, public_key)
        LOG.info("Amounts for bulk payout: {}".format(amounts))

        # Convert to HMT
        hmt_amounts = [int(amount * 10**18) for amount in amounts]
        return _bulk_payout_sol(self.job_contract, addresses, hmt_amounts, url,
                                hash_)

    def complete(self) -> bool:
        try:
            return _complete(self.job_contract)
        except Exception as e:
            LOG.error("Unable to complete contract:{} is the exception".format(
                str(e)))
            return False

    def get_manifest(self, private_key: bytes) -> dict:
        return download(_getURL(self.job_contract), private_key)

    def get_intermediate_results(self, private_key: bytes) -> dict:
        return download(_getIURL(self.job_contract), private_key)

    def get_results(self, private_key: bytes) -> dict:
        return download(_getFURL(self.job_contract), private_key)


def access_job(escrow_address: str, private_key: bytes,
               gas=DEFAULT_GAS) -> Contract:
    job = get_job_from_address(escrow_address)
    url = _getURL(job, gas=gas)
    manifest_dict = download(url, private_key)
    contract_m = Manifest(manifest_dict)
    contract = Contract(contract_m)
    per_job_cost = Decimal(manifest_dict['task_bid_price'])
    number_of_answers = int(manifest_dict['job_total_tasks'])
    oracle_stake = Decimal(manifest_dict['oracle_stake'])
    amount = Decimal(per_job_cost * number_of_answers)
    contract.initialize(job, amount, oracle_stake, number_of_answers)
    return contract


def get_job(gas=DEFAULT_GAS) -> str:
    """ Get a new job and launch it without funds on the blockchain.

        This is the first step of putting a new job on the blockchain.
        After this function is called the user can add funds, abort, or set the job up for pending.

        Args:
            gas (int): How much gas to get on the contract.
        Returns:
            Contract: The contract launched on the blockchain
            """

    global ESCROW_FACTORY
    factory = None
    if not ESCROW_FACTORY:
        factory = deploy_factory(gas)
        ESCROW_FACTORY = factory.address
        if not ESCROW_FACTORY:
            raise Exception("Unable to get address from factory")

    if factory is None:
        factory = get_factory(ESCROW_FACTORY)
        counter = factory.functions.getCounter().call({
            'from': GAS_PAYER,
            'gas': gas
        })
        LOG.debug("Factory counter is at:{}".format(counter))

    w3 = get_w3()
    nonce = w3.eth.getTransactionCount(GAS_PAYER)
    tx_dict = factory.functions.createEscrow().buildTransaction({
        'from': GAS_PAYER,
        'gas': gas,
        'nonce': nonce
    })
    tx_hash = sign_and_send_transaction(tx_dict, GAS_PAYER_PRIV)
    wait_on_transaction(tx_hash)

    escrow_address = factory.functions.getLastAddress().call({
        'from': GAS_PAYER,
        'gas': gas
    })

    LOG.info("New pokemon!:{}".format(escrow_address))
    return escrow_address


def get_job_from_address(escrow_address: str) -> Contract:
    return get_escrow(escrow_address)


def setup_job(contract: Contract, amount: Decimal, oracle_stake: Decimal,
              manifest_url: str, manifest_hash: str) -> bool:
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
    reputation_oracle = GAS_PAYER
    recording_oracle = GAS_PAYER
    reputation_oracle_stake = int(oracle_stake * 100)
    recording_oracle_stake = int(oracle_stake * 100)
    hmt_amount = int(amount * 10**18)

    return _setup_sol(contract, reputation_oracle, recording_oracle,
                      reputation_oracle_stake, recording_oracle_stake,
                      hmt_amount, manifest_url, manifest_hash)


def abort_job(contract: Contract, gas=DEFAULT_GAS) -> bool:
    """ Return all leftover funds to the contract launcher

        Once a job hash been put on blockchain, and is funded, this function can return
        the money to the funder of the contract. This function cannot run if the contract has
        already been partially paid.

        Args:
            contract (Contract): The actual ethereum contract instantiated.
            gas (int): The amount of gas to run the transaction with.
        Returns:
            bool: True if the contract is pending """
    return _abort_sol(contract, gas)


def store_results(contract: Contract,
                  manifest_url: str,
                  manifest_hash: str,
                  gas=DEFAULT_GAS) -> bool:
    """ Store intermediate results in the contract

        Store intermediate manifest results

        Args:
            contract (Contract): The actual ethereum contract instantiated.
            manifest_url (str): The url of the answers to the questions
            manifest_hash: The hash of the plaintext of the manifest.
            gas (int): The amount of gas to run the transaction with.
        Returns:
            bool: True if the results storage was successful """
    return _store_results(contract, manifest_url, manifest_hash, gas)


Status = Enum('Status', 'Launched Pending Partial Paid Complete Cancelled')


def status(contract: Contract, gas=DEFAULT_GAS) -> Enum:
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
    status_ = _status(contract, gas=gas)
    return Status(status_ + 1)
