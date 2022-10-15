# <img height="60px" src="./static/human.svg" alt="human" />
# Help Wanted!

Human Protocol’s bounty program is the easiest way to get a job working with us. Most of our development comes from the founders of hmt-escrow, bounties from open source developers, or developers hired from the bounty program. Take a look at our issues or suggest a new one, and a mod will add it to the bounty program. Read the documentation as it contains information for working with us.

Reward sizes are guided by the rules below and payable in USDC. If you prefer, you may also elect to have your reward donated to a registered charity of your choice that accepts online donations, subject to approval of the charity.

Read more on our [bug bounty page](https://www.humanprotocol.org/bug-bounty-program?lng=en-US)
## Installation

### Manual

You need few essential system requirements to successfully install our Python 3 package.

### Annoying testing feature

Rightly or Wrongly we tried to use doctests for the vast majority of testing in this project
. As a result you may have to remove the raise_on_error=True in the module you are testing
to get good feedback on what's broken.


#### Debian / Ubuntu

We'd recommend you checking out the dockerfile for an explanation of what applications are required

After that the following command should install the package successfully:

```
pip install git+https://github.com/iamdefinitelyahuman/py-solc-x@master#egg=py-solc-x \
            git+https://github.com/ethereum/trinity@master#egg=trinity \
            git+https://github.com/sphinx-doc/sphinx@master#egg=sphinx

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

Join our [Telegram](https://hmt.ai/telegram) channel, we will gladly answer your questions.

## Found a bug or a feature request?

Please search for any existing issues at our [Issues](https://github.com/humanprotocol/hmt-contracts/issues) page before submitting your own. If you submit your own, please follow our `Bug Request` and `Feature Request` templates.

Also check our [Bug Bounty Program](https://github.com/hCaptcha/bounties) and [Bounty Issues](https://github.com/humanprotocol/hmt-escrow/issues?q=is%3Aopen+is%3Aissue+label%3Abounty).

## Contributions

Interesting in contributing to the project? Please see our [Contributing guidelines](CONTRIBUTING.md) and check our instructions for setting up the project and getting your commits to the codebase.

## License

MIT © HUMAN Protocol

## Audit Status

The HUMAN Protocol token contract (HMToken.sol) has been audited by several third parties, most recently CertiK. You can see the results of this audit in the `audits` directory. The code for this contract is stable and not expected to change materially in the future.

The escrow factory and related code are under active development, and escrow factories on the testnet are frequently launched during development. 

Although all code goes through internal reviews before being committed, you should assume the current code in master has not been externally audited to the same degree as the token contract. 

When a stable 1.0 version of the escrow factory contract is released, this section of the README will be updated with a link to audit results for that githash.

## Note to bug hunters and those deploying to production

The docker-compose.yml references a default minio username and password for development. minio as used here is an internal cache for low-privilege, publicly readable, encrypted data. Including these default credentials for development is intentional. 

When deploying to a production environment you are expected to set your own credentials based on the rules applied to minio access within your cluster.


## Polygon deployment

```
Escrow Factory - 0x45eBc3eAE6DA485097054ae10BA1A0f8e8c7f794
Escrow Factory polygon-escrow-bulk branch https://github.com/humanprotocol/hmt-escrow/tree/polygon-escrow-bulk - 0xF09f451eC04cAb1b1FAe98C86F45291B00E52b03
KVStore - 0x6334dB76037bb6d4bc21901433E870b22ACa1F9a
HMToken - 0xc748B2A084F8eFc47E086ccdDD9b7e67aEb571Bf
```

## Polygon Mumbai Testnet

```
Escrow Factory - 0x558cd800f9F0B02f3B149667bDe003284c867E94
KVStore - 0x32e27177BA6Ea91cf28dfd91a0Da9822A4b74EcF
HMToken - 0x0376D26246Eb35FF4F9924cF13E6C05fd0bD7Fb4
```

## Moonbeam deployment

```
Escrow Factory - 0x98108c28B7767a52BE38B4860832dd4e11A7ecad
HMToken - 0x3b25BC1dC591D24d60560d0135D6750A561D4764
KVStore - 0x6617d21ab0f16A7079e2811Cf9306CAe7018bDd9
```

## Moonbase Alpha deployment

```
Escrow Factory - 0x3Cd0B117Be4CC1e31c8d7d1eD8b32208a2820902
HMToken - 0xe4C8eC5d057EacF40060b2174627a4941a5c8127
KVStore - 0x64009ca5fb4b34769F7240c6073FEc34bf5b64E3
```

## Neonlabs Devnet

```
Escrow Factory - 0x75D377773aCf9eB1076B01c1698415Bfe2db6D9d
KVStore - 0x2210c93c4fad2d8113035f6ec6e25d47be012604
HMToken - 0x2A78BA72f52Af2CC90c9389DbE0d2C4B10055b81
```

## Binance Smart Chain deployment

```
Escrow Factory - 0xc88bC422cAAb2ac8812de03176402dbcA09533f4
HMToken - 0x0d501B743F22b641B8C8dfe00F1AAb881D57DDC7
KVStore - 0x8340412Ed68BcF53a7Da72BFFc1E2E74CfdE74D0
```

## Binance Smart Chain Testnet deployment

```
Escrow Factory - 0xaae6a2646c1f88763e62e0cd08ad050ea66ac46f
HMToken - 0xd3a31d57fdd790725d0f6b78095f62e8cd4ab317
KVStore - 0x7676F326f1e30E96a76B7F1a860d56A9ac988a7d
```

## Maintainers

* Polygon : [foufrix](https://github.com/foufrix)
* Moonbeam: [menezesphill](https://github.com/menezesphill)
* Binance Smart Chain: [leetdev](https://github.com/leetdev)
