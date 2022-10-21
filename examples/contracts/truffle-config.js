module.exports = {
  networks: {
    development: {
     host: "0.0.0.0",
     port: 8547,
     network_id: "1337",
    },
  },

  compilers: {
    solc: {
      version: "0.6.2",
      settings: {
       optimizer: {
         enabled: false,
         runs: 200
       },
       evmVersion: "constantinople"
      }
    }
  },
};
