import { ethers } from "hardhat";
const fs = require('fs');
const path = require('path');


const ADDRESS_OUTPUT_FILENAME = '../hmt.address.json';

async function main() {
  const HMToken = await ethers.getContractFactory("HMToken");
  const HMTokenContract = await HMToken.deploy(1000000000, 'Human Token', 18, 'HMT');
  const token = await HMTokenContract.deployed();

  const fileContent = {
    address: token,
  };

  try {
    fs.mkdirSync(path.dirname(ADDRESS_OUTPUT_FILENAME));
  } catch (err: any) {
    if (err.code !== 'EEXIST') throw err;
  }

  fs.writeFile(ADDRESS_OUTPUT_FILENAME, JSON.stringify(fileContent, null, 2), (err: any) => {
    if (err) {
      console.error(`Unable to write address to output file: ${ADDRESS_OUTPUT_FILENAME}`);
    } else {
      console.log(`Deployed hmt token address stored in ${ADDRESS_OUTPUT_FILENAME}`);
    }
  });

  console.log("HMToken Address: ", token.address)
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});