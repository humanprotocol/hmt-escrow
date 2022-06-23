# humansubgraph

This is the repo of the human subgraph.
The goal of the subgraph is to index all of the emissions for Escrow and Escrow Factories
To get more information about how the graph works : https://thegraph.com/en/

## Installation

You need to install the Graph CLI to use and deploy the graph :

```sh
# NPM
npm install -g @graphprotocol/graph-cli
# Yarn
yarn global add @graphprotocol/graph-cli
```

### Run the graph locally


```sh
npm run create-local
```
This command will deploy the graph on your local environement

You can access it on  `http://localhost:8020/`


### Build the graph

```sh
npm run build
```
This command will build a production ready package of the graph. 

### Deploy the graph

```sh
npm run deploy
```
This command will build the graph and then deploy it on `https://api.thegraph.com/deploy/ posix4e/humansubgraph`

### Contracts compilation 

The compilation of the contracts is automatically made at the build. ABIs are generated from files (.sol) on `/contracts` folder. 
See `compile.js` file. 


Currently deploying to:

- main branch -> https://thegraph.com/hosted-service/subgraph/humanprotocol/polygon

- rinkeby branch -> https://thegraph.com/hosted-service/subgraph/humanprotocol/rinkeby
