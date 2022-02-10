# Fortune


An example human application for telling the future with 3 ethereum comptatible oracles. 

- Exchange Oracle
The entity which interacts with people or bots to fufill the task. In this case, a fortune teller tells fortune recorder.

- Recording Oracle
The entity which records the task output and who does what. In this case, a fortune recorder get the fortune from the fortune teller and remembers it.

- Reptutation Oracle
The entity which payes for the tasks based on the reputation in the oracle network. In this case, the fortune payer collects all the information from the fortune recorder and payes out the fortune teller and fortune recorder.

## Running Locally


```
docker-compose up
cd contracts && yarn && yarn deploy // this commands deploys contracts to the blockchain
```

In the [minio](http://localhost:9001) you will find a `manifests` bucket with `manifest.json` file, which we will use as an example manifest for the fortune app. Feel free to add your own manifest

Then you'll need to setup a network in the Metamask wallet. Add a new network with this parameters:
* Network Name - any name. We are using `Fortune Ganache` for this example
* New RPC URL - http://localhost:8547
* Chain ID - `1337`
* Currency Symbol - `ETH`

After that, add ganache accounts with their private keys to the metamask. These are accounts from the ganache dev setup
* `28e516f1e2f99e96a48a23cea1f94ee5f073403a1c68e818263f0eb898f1c8e5` - Account #1: A job requester
* `9e531b326f8c09437ab2af7a768e5e25422b43075169714f1790b6b036f73b00` - Account #2: An agent number 1
* `9da0d3721774843193737244a0f3355191f66ff7321e83eae83f7f746eb34350` - Account #3: An agent number 2

Use the Account #1 for deploying the job in the Job Launcher(http://localhost:3000)

Visit jobs launcher under http://localhost:3000

You can deploy a new job via `Create the Escrow` button. Or work with any existing Escrow in the network

After you put the Escrow address to the input, you will see it's status, info and other controls depending on the Escrow status.

In case it Launched - you should be able to fund the Escrow and setup it(by telling the Escrow oracle addresses, their stakes(in %) and the manifest URL)

To get the manifest URL - go to the [Minio](http://localhost:9001)(access = `dev`, secret = `devdevdev`) `manifests` bucket and get a shareable link to the `manifest.json` file(Share button).

After escrows will go to the Pending status - it will became available for exchanges. In the launcher there is a separate link which leads to the exchange http://localhost:3001.

After required fortunes are gathered - you will be able to see the Final Results URL in the launcher. 

**IMPORTANT NOTE**: Current setup with docker compose leads to the final results url with minio:9000 host inside. Which is inacessible from the localhost. So results could be found directly in the minio server under `job-results` bucket. The second way to overcome this - is to run each application without docker, which might lead to some changes in the compose file(for environment variables related to hosts)



Accounts addresses(For the ganache network)

* HMToken address - `0x444c45937D2202118a0FF9c48d491cef527b59dF`
* Escrow Factory Address - `0x3FF93a3847Cd1fa62DD9BcfE351C4b6BcCcF10cB`
* Recording Oracle Address - `0x61F9F0B31eacB420553da8BCC59DC617279731Ac`
* Reputation Oracle Address - `0xD979105297fB0eee83F7433fC09279cb5B94fFC6`
