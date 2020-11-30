const EscrowFactoryAbstraction = artifacts.require('EscrowFactory');
const HMTokenAbstraction = artifacts.require('HMToken');

let EscrowFactory;
let HMT;

contract('EscrowFactory', (accounts) => {
  const reputationOracle = accounts[2];
  const recordingOracle = accounts[3];
  const trustedHandlers = [reputationOracle, recordingOracle];

  beforeEach(async () => {
    HMT = await HMTokenAbstraction.new('100', 'Human Token', 4, 'HMT', { from: accounts[0] });
    EscrowFactory = await EscrowFactoryAbstraction.new(HMT.address, { from: accounts[0] });
  });

  it('sets eip20 address given to constructor', async () => {
    try {
      const address = await EscrowFactory.eip20.call();
      assert.equal(address, HMT.address);
    } catch (ex) {
      assert(false);
    }
  });
  describe('calling createEscrow', () => {
    it('creates new escrow contract', async () => {
      try {
        const escrow = await EscrowFactory.createEscrow(trustedHandlers, { from: accounts[0] });
        console.log(`CreateEscrow costs: ${escrow.receipt.gasUsed} wei.`);
        assert(escrow);
      } catch (ex) {
        assert(false);
      }
    });

    it('increases counter after new escrow is created', async () => {
      try {
        const initialCounter = await EscrowFactory.counter();
        assert.equal(initialCounter.toNumber(), 0);

        tx1 = await EscrowFactory.createEscrow(trustedHandlers, { from: accounts[0] });
        console.log(`CreateEscrow1 costs: ${tx1.receipt.gasUsed} wei.`);

        const counterAfterFirstEscrow = await EscrowFactory.counter();
        assert.equal(counterAfterFirstEscrow.toNumber(), 1);

        tx2 = await EscrowFactory.createEscrow(trustedHandlers, { from: accounts[0] });
        console.log(`CreateEscrow2 costs: ${tx2.receipt.gasUsed} wei.`);

        const counterAfterSecondEscrow = await EscrowFactory.counter();
        assert.equal(counterAfterSecondEscrow.toNumber(), 2);

        const totalGas = tx1.receipt.gasUsed + tx2.receipt.gasUsed;
        assert(totalGas <= 10000000, `Too much gas used: ${totalGas}. Should have used less than: ${10000000}`);
      } catch (ex) {
        assert(false);
      }
    });

    it('finds the newly created escrow from deployed escrow', async () => {
      try {
        const initialCounter = await EscrowFactory.counter();
        assert.equal(initialCounter.toNumber(), 0);

        tx = await EscrowFactory.createEscrow(trustedHandlers, { from: accounts[0] });
        console.log(`CreateEscrow costs: ${tx.receipt.gasUsed} wei.`);
        const escrowAddress = await EscrowFactory.lastEscrow();
        const hasEscrow = await EscrowFactory.hasEscrow(escrowAddress);
        assert.equal(hasEscrow, true);
      } catch (ex) {
        assert(false);
      }
    });
  });
});
