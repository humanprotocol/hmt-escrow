module.exports = {
  contracts_directory: './ganache/contracts',
  migrations_directory: './ganache/migrations',
  contracts_build_directory: './ganache/build',
  networks: {
    development: {
      host: 'ganache',
      port: 8545,
      network_id: '1337',
    }
  },
  compilers: {
    solc: {
      version: '0.6.2', // Fetch exact version from solc-bin (default: truffle's version)
      settings: {
        // See the solidity docs for advice about optimization and evmVersion
        optimizer: {
          enabled: true,
          runs: 200,
        },
        evmVersion: 'constantinople',
      },
    },
  },
};

