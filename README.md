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
