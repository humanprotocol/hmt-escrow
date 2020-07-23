require('dotenv').config()

const { INFURA_TOKEN, MNEMONIC, ETH_HOST, ETH_PORT } = process.env;
const HDWalletProvider = require('truffle-hdwallet-provider');

module.exports = {

  plugins: ["truffle-security, solidity-coverage"],

  networks: {
    development: {
      host: ETH_HOST || '127.0.0.1',
      port: ETH_PORT || 8545,
      network_id: '*'
    },
    live: {
      provider: () => new HDWalletProvider(MNEMONIC, `https://mainnet.infura.io/${INFURA_TOKEN}`),
      network_id: '1',
    },
    kovan: {
      provider: () => new HDWalletProvider(MNEMONIC, `https://kovan.infura.io/${INFURA_TOKEN}`),
      network_id: '2',
    },
    ropsten: {
      provider: () => new HDWalletProvider(MNEMONIC, `https://ropsten.infura.io/${INFURA_TOKEN}`),
      network_id: '3',
      gas: 4700000,
    },
    rinkeby: {
      provider: () => new HDWalletProvider(MNEMONIC, `https://rinkeby.infura.io/${INFURA_TOKEN}`),
      network_id: '4',
    },
  },
  compilers: {
    solc: {
      version: "0.6.2", // Fetch exact version from solc-bin (default: truffle's version)
      settings: {
        // See the solidity docs for advice about optimization and evmVersion
        optimizer: {
          enabled: true,
          runs: 200
        },
        evmVersion: "constantinople"
      }
    }
  }
};
