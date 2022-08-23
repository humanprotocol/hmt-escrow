const fs = require('fs');

const path = require('path');

const EscrowFactory = artifacts.require('./EscrowFactory.sol');

const ADDRESS_INPUT_FILENAME = './deployed-hmtoken/hmt.address.json';
const ADDRESS_OUTPUT_FILENAME = './deployed-escrow-factory/escrow-factory.address.json';

module.exports = (deployer) => {
  const { address } = JSON.parse(fs.readFileSync(ADDRESS_INPUT_FILENAME).toString());

  deployer
    .deploy(EscrowFactory, address)
    .then(() => {
      const fileContent = {
        address: EscrowFactory.address,
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
          console.log(`deployed escrow factory address stored in ${ADDRESS_OUTPUT_FILENAME}`);
        }
      });
    });
};
