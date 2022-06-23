/* eslint-disable no-unused-vars */
var fs = require("fs");
var networks = require("../networks.json");

async function replaceContractAddresses() {
  if (!process.argv[2]) {
    console.error("Missing network..");
    return;
  }

  const network = networks.find(net => net.name === process.argv[2]);
  if (!network) {
    console.error("Invalid network name :", process.argv[2]);
    return;
  }

  console.log("Creating subgraph.yaml for " + network.name);
  let subgraph = fs.readFileSync("./subgraph.template.yaml", "utf8");

  subgraph = subgraph.replace(/__NETWORK__/g, network.name);
  subgraph = subgraph.replace(/__DESCRIPTION__/g, network.description);

  // ESCROW FACTORY CONFIGURATION
  subgraph = subgraph.replace(
    /__STARTBLOCK_ESCROW_FACTORY__/g,
    network["EscrowFactory"].startBlock
  );
  subgraph = subgraph.replace(
    /__ESCROW_FACTORY_ADDRESS__/g,
    "'" + network["EscrowFactory"].address + "'"
  );

  // HMToken CONFIGURATION
  subgraph = subgraph.replace(
    /__HMTOKEN_ADDRESS__/g,
    network["HMToken"].address
  );
  subgraph = subgraph.replace(
    /__STARTBLOCK_HMTOKEN__/g,
    "'" + network["HMToken"].startBlock + "'"
  );

  fs.writeFileSync("subgraph.yaml", subgraph, "utf8");
}

replaceContractAddresses();
