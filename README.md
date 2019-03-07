# <img height="60px" src="./static/human.svg" alt="human" />

This repository features the library for launching and writing to HMT solidity contracts.

## Installation

We run the following version on Python 3.

### Manual

You need few essential system requirements to successfully install our python package.

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

After that the following command should install the package successfully.
```
pip install hmt-escrow
```
### Docker

In order to build the image you need [Docker](https://www.docker.com/) installed on your computer.

We have gathered relevant commands in the `bin/` folder.

You can run the project with `bin/prelaunch`.


### Getting Started

Creating a new Job requires a manifest and credentials at minimum. Optionally a factory address and/or an escrow address
can be given. Using an existing factory address can be used to deploy a new Job to the ethereum network. Using an existing
factory address and escrow address together can be accessed an existing job on the ethereum network. Creating a job without
a factory address deploys a fresh factory to the ethereum network.

A Manifest has to follow the specification at https://github.com/hCaptcha/hmt-basemodels
Credentials have to follow the following format:
```
>>> credentials = {
... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
... }
>>> rep_oracle_pub_key = b"2dbc2c2c86052702e7c219339514b2e8bd4687ba1236c478ad41b43330b08488c12c8c1797aa181f3a4596a1bd8a0c18344ea44d6655f61fa73e56e743f79e0d"
```

Using only the manifest and credentials deploys a new factory to the ethereum network
with the public key of a known Reputation Oracle.
```
>>> job = Job(manifest, credentials)
>>> job.launch(rep_oracle_pub_key)
True
```

Providing an existing factory address is set to Job's class attributes.
```
>>> factory_addr = deploy_factory(**credentials)
>>> job = Job(manifest, credentials, factory_addr)
>>> job.launch(rep_oracle_pub_key)
True
```

Providing an existing factory address and a factory address are automatically set to
Job's class attributes. Credentials have to contain the private key that was used to upload
the previously deployed manifest to IPFS. The Job is instantiated with the fetched
manifest. An accessed job can't be launched anymore.

```
>>> credentials = {
... 	"gas_payer": "0x1413862C2B7054CDbfdc181B83962CB0FC11fD92",
... 	"gas_payer_priv": "28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5",
...     "rep_oracle_priv_key": b"28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5"
... }

>>> factory_addr = deploy_factory(**credentials)
>>> escrow_addr = job.job_contract.address

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
Partial state. It alsoo uploads the final results from the Reputation Oracle to the contract's
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

Completing the job sets a paid contract to complete.
```
>>> job.complete()
True
>>> job.status()
<Status.Partial: 5>
```

## Deploying to PyPi

A build will automatically be deployed to PyPi from master if tagged with a version number.  This version number should also match the version in the `setup.py` file.

The tags will need to be pushed via a user that has the proper privileges to master (see the contributors of this repo).  

Versioning should follow the [semver](https://semver.org/) versioning methodology and not introduce breaking changes on minor or patch-level changes.

## Have a question?

Join our [Telegram](https://t.me/hcaptchachat) channel, we will gladly answer your questions.

## Found a bug?

Please search for any existing issues at our [Issues](https://github.com/IntuitionMachines/hmt-contracts/issues) page before submitting your own.

Also check our [Bug Bounty Program](https://github.com/hCaptcha/bounties).

## Contributions

Interesting in contributing to the project? Please see our [Contributing guidelines](CONTRIBUTING.md) and check our instructions for setting up the project and getting your commits to the codebase.

## License

MIT © HUMAN Protocol
