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

## 🏊 Deploying graphs for live networks

1. Generate & deploy on matic

```bash
npm run quickstart:matic
```

2. Generate & deploy on rinkeby

```bash
npm run quickstart:rinkeby
```

You can access it on `http://localhost:8020/`

### Build and deploy the graph

This deploiement of the graph on each network is automatically triggered by the github CI

### Contracts compilation

The compilation of the contracts is automatically made at the build. ABIs are generated from files (.sol) on `/contracts` folder.
See `compile.js` file.

Currently deploying to:

- main branch -> https://thegraph.com/hosted-service/subgraph/humanprotocol/polygon

- rinkeby branch -> https://thegraph.com/hosted-service/subgraph/humanprotocol/rinkeby
