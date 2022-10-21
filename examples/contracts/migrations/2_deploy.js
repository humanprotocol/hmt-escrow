const HMToken = artifacts.require('HMToken');
const EscrowFactory = artifacts.require('EscrowFactory');

module.exports = async function (deployer) {
  await deployer.deploy(HMToken, "1000000000", "Human Token", "18", "HMT");
  await deployer.deploy(EscrowFactory, HMToken.address);
};