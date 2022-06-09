const EscrowFactoryAbstraction = artifacts.require('EscrowFactory');
const HMTokenAbstraction = artifacts.require('HMToken');

let EscrowFactoryTest;
let HMT;

contract('EscrowFactory', (accounts) => {
  const reputationOracle = accounts[2];
  const recordingOracle = accounts[3];
  const trustedHandlers = [reputationOracle, recordingOracle];

  beforeEach(async () => {
    HMT = await HMTokenAbstraction.new('100', 'Human Token', 4, 'HMT', { from: accounts[0] });
    EscrowFactoryTest = await EscrowFactoryAbstraction.new(HMT.address, { from: accounts[0] });
  });

  it('sets eip20 address given to constructor', async () => {
    try {
      const address = await EscrowFactoryTest.eip20.call();
      assert.equal(address, HMT.address);
    } catch (ex) {
      assert(false);
    }
  });
  describe('calling createEscrow', () => {
    it('creates new escrow contract', async () => {
      try {
        const escrow = await EscrowFactoryTest.createEscrow(trustedHandlers, { from: accounts[0] });
        console.log(`CreateEscrow costs: ${escrow.receipt.gasUsed} wei.`);
        assert(escrow);
      } catch (ex) {
        assert(false);
      }
    });

    it('increases counter after new escrow is created', async () => {
      try {
        const initialCounter = await EscrowFactoryTest.counter();
        assert.equal(initialCounter.toNumber(), 0);

        tx1 = await EscrowFactoryTest.createEscrow(trustedHandlers, { from: accounts[0] });
        console.log(`CreateEscrow1 costs: ${tx1.receipt.gasUsed} wei.`);

        const counterAfterFirstEscrow = await EscrowFactoryTest.counter();
        assert.equal(counterAfterFirstEscrow.toNumber(), 1);

        tx2 = await EscrowFactoryTest.createEscrow(trustedHandlers, { from: accounts[0] });
        console.log(`CreateEscrow2 costs: ${tx2.receipt.gasUsed} wei.`);

        const counterAfterSecondEscrow = await EscrowFactoryTest.counter();
        assert.equal(counterAfterSecondEscrow.toNumber(), 2);

        const totalGas = tx1.receipt.gasUsed + tx2.receipt.gasUsed;
        assert(totalGas <= 10000000, `Too much gas used: ${totalGas}. Should have used less than: ${10000000}`);
      } catch (ex) {
        assert(false);
      }
    });

    it('finds the newly created escrow from deployed escrow', async () => {
      try {
        const initialCounter = await EscrowFactoryTest.counter();
        assert.equal(initialCounter.toNumber(), 0);

        tx = await EscrowFactoryTest.createEscrow(trustedHandlers, { from: accounts[0] });
        console.log(`CreateEscrow costs: ${tx.receipt.gasUsed} wei.`);
        const escrowAddress = await EscrowFactoryTest.lastEscrow();
        const hasEscrow = await EscrowFactoryTest.hasEscrow(escrowAddress);
        assert.equal(hasEscrow, true);
      } catch (ex) {
        assert(false);
      }
    });
  });
});
