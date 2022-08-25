const fs = require('fs');

const path = require('path');

const HMToken = artifacts.require('./HMToken.sol');
const EscrowFactory = artifacts.require('./EscrowFactory.sol');

const TOKEN_ADDRESS_OUTPUT_FILENAME = './deployed-hmtoken/hmt.address.json';
const FACTORY_ADDRESS_OUTPUT_FILENAME = './deployed-escrow-factory/escrow-factory.address.json';

const saveAddress = (address, filename) => {
  const fileContent = { address };

  try {
    fs.mkdirSync(path.dirname(filename));
  } catch (err) {
    if (err.code !== 'EEXIST') throw err;
  }

  fs.writeFile(filename, JSON.stringify(fileContent, null, 2), (err) => {
    if (err) {
      console.error(`unable to write address to output file: ${filename}`);
    } else {
      console.log(`deployed contract address stored in ${filename}`);
    }
  });
}

module.exports = async (deployer) => {
  await deployer.deploy(HMToken, 1000000000, 'Human Token', 18, 'HMT');
  saveAddress(HMToken.address, TOKEN_ADDRESS_OUTPUT_FILENAME);

  await deployer.deploy(EscrowFactory, HMToken.address);
  saveAddress(EscrowFactory.address, FACTORY_ADDRESS_OUTPUT_FILENAME);
};
