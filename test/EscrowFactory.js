const EscrowFactoryAbstraction = artifacts.require('EscrowFactory');
const HMTokenAbstraction = artifacts.require('HMToken');

let EscrowFactory;
let HMT;

contract('EscrowFactory', (accounts) => {
  const reputationOracle = accounts[2];
  const recordingOracle = accounts[3];
  const trustedHandlers = [reputationOracle, recordingOracle]

  beforeEach(async () => {
    HMT = await HMTokenAbstraction.new('100', 'Human Token', 4, 'HMT', { from: accounts[0] });
    EscrowFactory = await EscrowFactoryAbstraction.new(HMT.address, { from: accounts[0] });
  });

  it('sets eip20 address given to constructor', async () => {
    try {
      const address = await EscrowFactory.getEIP20.call();
      assert.equal(address, HMT.address);
    } catch (ex) {
      assert(false);
    }
  });
  describe('calling createEscrow', () => {
    it('creates new escrow contract', async () => {
      try {
        const escrow = await EscrowFactory.createEscrow(trustedHandlers, { from: accounts[0] });
        assert(escrow);
      } catch (ex) {
        assert(false);
      }
    });

    it('increases counter after new escrow is created', async () => {
      try {
        const initialCounter = await EscrowFactory.getCounter();
        assert.equal(initialCounter.toNumber(), 0);

        await EscrowFactory.createEscrow(trustedHandlers, { from: accounts[0] });

        const counterAfterFirstEscrow = await EscrowFactory.getCounter();
        assert.equal(counterAfterFirstEscrow.toNumber(), 1);

        await EscrowFactory.createEscrow(trustedHandlers, { from: accounts[0] });

        const counterAfterSecondEscrow = await EscrowFactory.getCounter();
        assert.equal(counterAfterSecondEscrow.toNumber(), 2);
      } catch (ex) {
        assert(false);
      }
    });

    it('finds the newly created escrow from deployed escrow', async () => {
      try {
        const initialCounter = await EscrowFactory.getCounter();
        assert.equal(initialCounter.toNumber(), 0);

        await EscrowFactory.createEscrow(trustedHandlers, { from: accounts[0] });
        const escrowAddress = await EscrowFactory.getLastEscrow();
        const hasEscrow = await EscrowFactory.hasEscrow(escrowAddress);
        assert.equal(hasEscrow, true);
      } catch (ex) {
        assert(false);
      }
    });
  });
});
