const fs = require('fs');

const path = require('path');

const HMToken = artifacts.require('./HMToken.sol');
const EscrowFactory = artifacts.require('./EscrowFactory.sol');

const ADDRESS_OUTPUT_FILENAME = './deployed-contracts/contract.addresses.json';

module.exports = async function (deployer) {
  await deployer
    .deploy(HMToken, 1000000000, 'Human Token', 18, 'HMT');


  await deployer.deploy(EscrowFactory, HMToken.address)
    .then(() => {
      const fileContent = {
        HMTAddress: HMToken.address,
        EscrowFactory: EscrowFactory.address,
      };

      try {
        fs.mkdirSync(path.dirname(ADDRESS_OUTPUT_FILENAME));
      } catch (err) {
        if (err.code !== 'EEXIST') throw err;
      }

      fs.writeFile(ADDRESS_OUTPUT_FILENAME, JSON.stringify(fileContent, null, 2), (err) => {
        if (err) {
          console.error(`unable to write address to output file: ${ADDRESS_OUTPUT_FILENAME}`);
        } else {
          console.log(`deployed hmt token address stored in ${ADDRESS_OUTPUT_FILENAME}`);
        }
      });
    });
};
