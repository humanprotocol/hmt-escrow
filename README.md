# <img height="60px" src="./static/human.svg" alt="human" />

This repository contains a Python 3 library for launching and communicating with HMT Solidity contracts.

## Installation

### Manual

You need few essential system requirements to successfully install our Python 3 package.

#### Debian / Ubuntu

```
build-essential 
libffi
autoconf 
libtool
pkg-config
```

#### macOS

```
automake
pkg-config
libtool
libffi
gmp
```

After that the following command should install the package successfully:
```
pip install hmt-escrow
```
### Docker

In order to build the image you need [Docker](https://www.docker.com/) installed on your computer.

We have gathered relevant commands in the `bin/` folder.

You can run the project with `bin/prelaunch`.


### Getting Started

Creating a new HUMAN Protocol Job requires a manifest and credentials at minimum. Optionally a factory 
address and/or an escrow address can be given. Using an existing factory address can be used to deploy 
a new Job to the Ethereum network. Using an existing factory address and escrow address together an 
existing Job on the Ethereum network can be accessed. Creating a Job without a factory address deploys 
a fresh factory to the Ethereum network.

A Manifest has to follow the specification at https://github.com/hCaptcha/hmt-basemodels

Credentials must follow the following format:
```
>>> credentials = {
... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
... }
>>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
```

Using only the Manifest and Credentials deploys a new factory to the Ethereum network
with the public key of a known Reputation Oracle.
```
>>> job = Job(credentials, manifest)
>>> job.launch(rep_oracle_pub_key)
True
```

Providing an existing factory address is done via the Job's class attributes.
```
>>> factory_addr = deploy_factory(**credentials)
>>> job = Job(credentials, manifest, factory_addr)
>>> job.launch(rep_oracle_pub_key)
True
```

You can supply an existing escrow factory address when instantiating the class, which 
it will use to do all operations. If an escrow factory address is not given, it creates one. 

Credentials have to contain the private key that was used to upload
the previously deployed manifest to IPFS. The Job is instantiated with the fetched
manifest.

```
>>> credentials = {
... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
...     "rep_oracle_priv_key": b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
... }

>>> factory_addr = deploy_factory(**credentials)
>>> escrow_addr = job.job_contract.address
```

If you provide an `escrow_addr` and a `factory_addr` the library will check 
whether that `escrow_addr` belongs to the `factory_addr`. If that succeeds 
you can continue from the state the contract is in.

A Job can only be launched once: calling `launch()` will return False if
you previously launched it.

```
>>> accessed_job = Job(credentials=credentials, factory_addr=factory_addr, escrow_addr=escrow_addr)
>>> accessed_job.launch(rep_oracle_pub_key)
False
```

Calling setup funds the deployed escrow contract and updates its state with data from the manifest.
```
>>> job.setup()
True
```

While no payouts have been performed, aborting and canceling a job is still possible.
```
>>> job.abort()
True
>>> job.cancel()
True
```

Performing a bulk payout that doesn't fully drain the escrow contract sets the contract to
Partial state. It also uploads the final results from the Reputation Oracle to the contract's
state.
```
>>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('20.0'))]
>>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
True
>>> job.status()
<Status.Partial: 3>
```

Draining the escrow contract fully sets the contract to Paid state.
```
>>> payouts = [("0x6b7E3C31F34cF38d1DFC1D9A8A59482028395809", Decimal('80.0'))]
>>> job.bulk_payout(payouts, {}, rep_oracle_pub_key)
True
>>> job.status()
<Status.Paid: 4>
```

Completing the job sets a Paid contract to complete.
```
>>> job.complete()
True
>>> job.status()
<Status.Partial: 5>
```

## Note for maintainers: Deploying to PyPi

A build will automatically be deployed to PyPi from master if tagged with a version number.  This version number should  match the version in the `setup.py` file.

The tags will need to be pushed to master via a user that has the proper privileges (see the contributors of this repo).  

Versioning should follow the [semver](https://semver.org/) versioning methodology and not introduce breaking changes on minor or patch-level changes.

## Have a question?

Join our [Telegram](https://t.me/hcaptchachat) channel, we will gladly answer your questions.

## Found a bug or a feature request?

Please search for any existing issues at our [Issues](https://github.com/IntuitionMachines/hmt-contracts/issues) page before submitting your own. If you submit your own, please follow our `Bug Request` and `Feature Request` templates.

Also check our [Bug Bounty Program](https://github.com/hCaptcha/bounties) and [Bounty Issues](https://github.com/hCaptcha/hmt-escrow/issues?q=is%3Aopen+is%3Aissue+label%3Abounty).

## Contributions

Interesting in contributing to the project? Please see our [Contributing guidelines](CONTRIBUTING.md) and check our instructions for setting up the project and getting your commits to the codebase.

## License

MIT © HUMAN Protocol

## Audit Status

The HUMAN Protocol token contract (HMToken.sol) has been audited by several third parties, most recently CertiK. You can see the results of this audit in the `audits` directory. The code for this contract is stable and not expected to change materially in the future.

The escrow factory and related code are under active development, and escrow factories on the testnet are frequently launched during development. 

Although all code goes through internal reviews before being committed, you should assume the current code in master has not been externally audited to the same degree as the token contract. 

When a stable 1.0 version of the escrow factory contract is released, this section of the README will be updated with a link to audit results for that githash.
