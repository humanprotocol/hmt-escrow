# Job Launcher Server
Pre-reading: https://github.com/humanprotocol/.github/wiki

## Overview
HUMAN is a multi-chain protocol with hundreds of thousands of decentralized workers operating across multiple chains. Anyone can assume the role of a worker and be paid for performing tasks.
Job requesters (people who want work performed) can launch jobs into the network and the jobs will be completed by workers. At a high level the HUMAN Protocol consists of two layers, the Routing Layer and the Execution Layer. The routing layer is responsible for routing jobs to the Layer 1 chains that offer the best execution terms (e.g tx cost, speed, liquidity). The execution layer is responsible for distributing individual tasks within a job to workers, verifying the results of those tasks, maintaining a reputation system for workers and remunerating workers for completed tasks. The two layers work together to facilitate the creation and completion of Jobs in the HUMAN Network.

## Job Launcher
This repository contains the HUMAN Job Launcher Server, an open source and multi-chain application that can be used to launch jobs into the HUMAN network. Job Launchers may be operated by organizations, institutions and individuals who earn rewards and commission for the services they provide. There are many Job Launchers within the HUMAN network and each one can provide specialized services (i.e different job types). You can view all existing Job Launchers operating on the HUMAN network by checking out the Leaderboard page: ADD LINK This particular version of the job launcher is focused on data labeling services. A job launcher operator will provide this service to the community. Job requesters can then use this service to upload raw images, which will ultimately be annotated by real HUMANS. We expect this repository to be modified and extended to other use cases.

## Tokenomics Model (Incentivization Mechanisms)
The open nature of the HUMAN Protocol means that any person or organization may operate core infrastructure and earn rewards for doing so. To prevent participants from acting maliciously, we have created a staking contract which requires all operators within the ecosystem to stake a security collateral. This is called Proof Of Balance. Any operator who is found to be breaching these rules will have their stake reduced by a predetermined amount, this is known as slashing.

## Software Requirements
The Job Launcher Server requires of a number key components, before installing the Server you should ensure you have completed the pre-install steps below.

1. Node.js and NPM
To see if you have installed Node.js and npm, execute the following commands in your terminal:

`node -v`

`npm -v`

If you do not have these installed you can follow the guide here:
https://docs.npmjs.com/downloading-and-installing-node-js-and-npm

2. Postgres Database
The server uses postgres as a database to store user emails and passwords.  Ensure that you have installed postgres and created a database before installing the actual server itself.  For postgres install instructions see here: 
https://www.postgresql.org/download/ 

Make a note of the postgres username, password and database name. 

3. Hardhat
Hardhat is an Ethereum development environment. Compile your contracts and run them on a development network. How to use Hardhat see here:
https://hardhat.org/hardhat-runner/docs/getting-started#quick-start

4. Postmark 
Postmark helps deliver and track application email. In a nutshell, the service replaces SMTP (or Sendmail) with a far more reliable, scalable and care-free environment. The Server uses Postmark to send out confirmation emails for new user sign ups and password resets.  Go to www.postmarkapp.com and sign up for a free account.  Once signed up head over to API tokens and note down your Server API Token.

5. AWS credentials
The server uses AWS S3 to store job details.  To setup an S3 bucket and generate the API Key & Secret follow this guide: https://medium.com/@shamnad.p.s/how-to-create-an-s3-bucket-and-aws-access-key-id-and-secret-access-key-for-accessing-it-5653b6e54337 

Take a note of the AWS region for the S3 bucket you just created, your API Key and Secret.

## Installation
6. When installing for the first time it will be necessary to run a database migration.  To do so you should set execute the following command in your terminal:

`export MIGRATIONS_RUN=true`


7. Clone this repo to your local machine and change directory into the cloned repo:
   
`git clone git@github.com:humanprotocol/job-launcher-server.git && cd job-launcher-server` 


8. Install using npm
   
`npm i`

9. Populate the .env file with the values you noted down in steps 2, 3 and 4.  

Postgres - you will need to update the following fields:
POSTGRES_USER=<ENTER USERNAME>
POSTGRES_PASSWORD=<ENTER PASSWORD >
POSTGRES_DB=<ENTER DB NAME>

Postmark - update with your API key from step 4
POSTMARK_API_KEY=<YOUR POSTMARK API KEY>
EMAIL_FROM=<ENTER YOUR FROM EMAIL>

AWS S3 API Key and Secret:
AWS_ACCESS_KEY_ID=<ENTER YOUR API ACCESS KEY>
AWS_SECRET_ACCESS_KEY=<ENTER YOUR API SECRET KEY>
AWS_REGION=<<ENTER AWS S3 BUCKET REGION>>
