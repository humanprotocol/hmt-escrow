const fs = require('fs');

const path = require('path');

const skaleStorage = artifacts.require('./SkaleStorage.sol');

const ADDRESS_OUTPUT_FILENAME = '/skale/SkaleStorage.address.json';

module.exports = (deployer) => {
  deployer
    .deploy(skaleStorage)
    .then(() => {
      const fileContent = {
        address: skaleStorage.address,
      };

      // try {
      //   fs.mkdirSync(path.dirname(ADDRESS_OUTPUT_FILENAME));
      // } catch (err) {
      //   if (err.code !== 'EEXIST') throw err;
      // }

      fs.writeFile(ADDRESS_OUTPUT_FILENAME, JSON.stringify(fileContent, null, 2), (err) => {
        if (err) {
          console.error(`unable to write address to output file: ${ADDRESS_OUTPUT_FILENAME}`);
        } else {
          console.log(`deployed SKALE storage address stored in ${ADDRESS_OUTPUT_FILENAME}`);
        }
      });
    });
};
