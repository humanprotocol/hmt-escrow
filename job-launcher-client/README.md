# Job Launcher Client App

Pre-reading: https://github.com/humanprotocol/.github/wiki

## Overview

HUMAN is a multi-chain protocol with hundreds of thousands of decentralized workers operating across multiple chains. Anyone can assume the role of a worker and be paid for performing tasks.  
Job requesters (people who want work performed) can launch jobs into the network and the jobs will be completed by workers. At a high level the HUMAN Protocol consists of two layers, the Routing Layer and the Execution Layer. The routing layer is responsible for routing jobs to the Layer 1 chains that offer the best execution terms (e.g tx cost, speed, liquidity). The execution layer is responsible for distributing individual tasks within a job to workers, verifying the results of those tasks, maintaining a reputation system for workers and remunerating workers for completed tasks. The two layers work together to facilitate the creation and completion of Jobs in the HUMAN Network.

## Job Launcher

This repository contains the HUMAN Job Launcher, an open source and multi-chain application that can be used to launch jobs into the HUMAN network. Job Launchers may be operated by organizations, institutions and individuals who earn rewards and commission for the services they provide. There are many Job Launchers within the HUMAN network and each one can provide specialized services (i.e different job types). You can view all existing Job Launchers operating on the HUMAN network by checking out the Leaderboard page: ADD LINK
This particular version of the job launcher is focused on data labeling services. A job launcher operator will provide this service to the community. Job requesters can then use this service to upload raw images, which will ultimately be annotated by real HUMANS.
We expect this repository to be modified and extended to other use cases.

## Tokenomics Model (Incentivization Mechanisms)

The open nature of the HUMAN Protocol means that any person or organization may operate core infrastructure and earn rewards for doing so. To prevent participants from acting maliciously, we have created a staking contract which requires all operators within the ecosystem to stake a security collateral. This is called Proof Of Balance. Any operator who is found to be breaching these rules will have their stake reduced by a predetermined amount, this is known as slashing.

## Installation

Note - This repo is just a front end and must be used in conjunction with the Job Launcher Server: https://github.com/humanprotocol/job-launcher-server
Follow the instructions to install and start in the Job Launcher Server repository. Once the server is started take a note of the Job Launcher API URL and continue with the instructions below.

1. Clone this repository:

`git clone https://github.com/humanprotocol/job-launcher-client`

2. Change into the cloned folder and install using yarn:

`cd job-launcher-client`
`yarn`

3. Update the environment variable. Rename the .env.example file in the root of this repo:

`cp .env.example .env`

The .env file contains the following variable:

- `REACT_APP_API_URL`: Job Launcher API
- `REACT_APP_JOB_LAUNCHER_ADDRESS`: Job Launcher contract ADDRESS
- `REACT_APP_HMT_TOKEN_ADDRESS`: Human hmt token contract ADDRESS

### Environment variables:

Normally, CRA uses .env file and REACT*APP*_ templates for environment variables. They are passed to the build phase
of the app and are injected directly to the build. This is not very convinient when we want to redeploy the app
by changing one or several variable.
Considering all REACT*APP*_ env variables as application variables we can assume that by changing
them the build should not be changed. So, all REACT*APP*\* env variables are injected into `window.env` properties.
For env variables access only window.env should be used instead of process.env

### Running in the production:

`cp .env.example .env`

`yarn`

`yarn build`

## Found a bug?

Please search for any existing issues at our [Issues](https://github.com/humanprotocol/job-launcher-client) page before submitting your own.
