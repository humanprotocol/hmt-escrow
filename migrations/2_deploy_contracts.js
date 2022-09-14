const fs = require('fs');

const path = require('path');

const HMToken = artifacts.require('./HMToken.sol');

const ADDRESS_OUTPUT_FILENAME = '/deployed-hmtoken/hmt.address.json';

module.exports = (deployer) => {
  deployer
    .deploy(HMToken, 1000000000, 'Human Token', 18, 'HMT')
    .then(() => {
      const fileContent = {
        address: HMToken.address,
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
