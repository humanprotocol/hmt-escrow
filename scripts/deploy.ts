import { ethers } from "hardhat";

const fs = require("fs");
const path = require("path");

const ADDRESS_OUTPUT_FILENAME = "../hmt.address.json";

async function main() {
  // Deploy HMT token
  const HMToken = await ethers.getContractFactory("HMToken");
  const HMTokenContract = await HMToken.deploy(
    1000000000,
    "Human Token",
    18,
    "HMT"
  );
  const token = await HMTokenContract.deployed();

  // Deploy Escrow Factory Contract
  const EscrowFactory = await ethers.getContractFactory("EscrowFactory");
  const EscrowFactoryContract = await EscrowFactory.deploy(token.address);
  const escrowFactory = await EscrowFactoryContract.deployed();

  // Deploy Staking Conract
  const minimumStake = 1;
  const lockPeriod = 2;
  const Staking= await ethers.getContractFactory("Staking");
  const StakingContract = await Staking.deploy(token.address, escrowFactory.address, minimumStake, lockPeriod);
  const staking = await StakingContract.deployed();

  // Deploy Staking Conract
  const RewardPool= await ethers.getContractFactory("RewardPool");
  const RewardPoolContract = await RewardPool.deploy(token.address, staking.address, 1);
  const rewardPool = await RewardPoolContract.deployed();

  console.log("HMToken Address: ", token.address)
  console.log("Escrow Factory Address: ", escrowFactory.address)
  console.log("Staking Address: ", staking.address)
  console.log("Reward Pool Address: ", rewardPool.address)

  const fileContent = {
    address: token,
  };

  try {
    fs.mkdirSync(path.dirname(ADDRESS_OUTPUT_FILENAME));
  } catch (err: any) {
    if (err.code !== "EEXIST") throw err;
  }

  fs.writeFile(
    ADDRESS_OUTPUT_FILENAME,
    JSON.stringify(fileContent, null, 2),
    (err: any) => {
      if (err) {
        console.error(
          `Unable to write address to output file: ${ADDRESS_OUTPUT_FILENAME}`
        );
      } else {
        console.log(
          `Deployed hmt token address stored in ${ADDRESS_OUTPUT_FILENAME}`
        );
      }
    }
  );

  console.log("HMToken Address: ", token.address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
