const EscrowFactoryAbstraction = artifacts.require('EscrowFactory');
const HMTokenAbstraction = artifacts.require('HMToken');

let EscrowFactory;
let HMT;

contract('EscrowFactory', (accounts) => {
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

  it('creates new escrow contract when calling createEscrow', async () => {
    try {
      const escrow = await EscrowFactory.createEscrow({ from: accounts[0] });
      assert(escrow);
    } catch (ex) {
      assert(false);
    }
  });

  it('increases counter when creating a new escrow', async () => {
    try {
      initialCounter = await EscrowFactory.getCounter();
      assert.equal(initialCounter.toNumber(), 0);

      await EscrowFactory.createEscrow({ from: accounts[0] });

      counterAfterFirstEscrow = await EscrowFactory.getCounter();
      assert.equal(counterAfterFirstEscrow.toNumber(), 1);

      await EscrowFactory.createEscrow({ from: accounts[0] });

      counterAfterSecondEscrow = await EscrowFactory.getCounter();
      assert.equal(counterAfterSecondEscrow.toNumber(), 2);
    } catch (ex) {
      assert(false);
    }
  })
});
