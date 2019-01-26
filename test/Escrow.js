const EscrowAbstraction = artifacts.require('Escrow');
const HMTokenAbstraction = artifacts.require('HMToken');

let Escrow;
let HMT;
let reputationOracle;
let recordingOracle;
const url = 'http://google.com/fake';
const hash = 'fakehash';

contract('Escrow', (accounts) => {
  beforeEach(async () => {
    HMT = await HMTokenAbstraction.new('100', 'Human Token', 4, 'HMT', { from: accounts[0] });
    reputationOracle = accounts[1];
    recordingOracle = accounts[2];

    Escrow = await EscrowAbstraction.new(HMT.address, accounts[0], 5, { from: accounts[0] });
  });

  describe('calling getTokenAddress', () => {
    it('returns correct token address', async () => {
      try {
        const address = await Escrow.getTokenAddress.call();
        assert.equal(address, HMT.address);
      } catch (ex) {
        assert(false);
      }
    });
  });

  describe('initial', () => {
    it('status is launched', async () => {
      try {
        const initialStatus = await Escrow.getStatus.call();
        assert.equal(0, initialStatus);
      } catch (ex) {
        assert(false);
      }
    });

    it('balance is 0', async () => {
      try {
        const initialBalance = await Escrow.getBalance.call();
        assert.equal(initialBalance.toNumber(), 0);
      } catch (ex) {
        assert(false);
      }
    });
  });

  it('transfering money to escrow increases balance', async () => {
    try {
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      const balance = await Escrow.getBalance.call();
      assert.equal(balance.toNumber(), 100);
    } catch (ex) {
      assert(false);
    }
  });

  describe('calling abort', () => {
    it('succeeds when aborting with same address', async () => {
      try {
        await Escrow.abort({ from: accounts[0] });
        assert(true);
      } catch (ex) {
        assert(false);
      }
    });

    it('fails when aborting with different address', async () => {
      try {
        await Escrow.abort({ from: accounts[1] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });
  });

  describe('calling setup', () => {
    it('fails when calling with different address than the contract was created with', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[1] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if reputation oracle or recording oracle stake is too high', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 500, 500, 10, url, hash, { from: accounts[1] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if reputation oracle or recording oracle stake is too low', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 0, 0, 10, url, hash, { from: accounts[1] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if contract has sufficient funds', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('sets parameters correctly', async () => {
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
      const contractReputationOracle = await Escrow.getReputationOracle.call();
      const contractRecordingOracle = await Escrow.getRecordingOracle.call();
      const contractUrl = await Escrow.getUrl.call();
      const contractHash = await Escrow.getHash.call();

      assert.equal(contractReputationOracle, reputationOracle);
      assert.equal(contractRecordingOracle, recordingOracle);
      assert.equal(contractUrl, url);
      assert.equal(contractHash, hash);
    });

    it('sets status to pending', async () => {
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
      const status = await Escrow.getStatus.call();
      assert.equal(1, status);
    });
  });

  describe('calling complete', () => {
    it('fails if trying to complete with other than reputation oracle address', async () => {
      try {
        await Escrow.complete({ from: accounts[0] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if escrow status is not complete or paid', async () => {
      try {
        await Escrow.complete({ from: reputationOracle });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });
  });

  describe('calling storeResults', () => {
    it('fails if calling address is not recording oracle', async () => {
      try {
        await Escrow.storeResults('url', 'hash', { from: accounts[0] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if status is other than pending or partial', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 0, url, hash, { from: accounts[0] });
        await Escrow.storeResults('url', 'hash', { from: accounts[2] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('succeeds if status is pending', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 0, url, hash, { from: accounts[0] });
        await Escrow.storeResults(url, hash, { from: accounts[2] });
        const IUrl = await Escrow.getIUrl.call();
        const IHash = await Escrow.getIHash.call();
        assert.equal(IUrl, url);
        assert.equal(IHash, hash);
      } catch (ex) {
        assert(false);
      }
    });

    it('sets status to complete after succesful payout', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        await Escrow.payOut(100, accounts[3], url, hash, { from: reputationOracle });
        await Escrow.complete({ from: reputationOracle });
        const contractStatus = await Escrow.getStatus.call();
        assert.equal(contractStatus.toNumber(), 4);
      } catch (ex) {
        assert(false);
      }
    });
  });

  describe('calling payOut', () => {
    it('fails if escrow status is not yet setup', async () => {
      try {
        await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if contract is out of funds', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 0, url, hash, { from: accounts[0] });
        await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });
  });

  describe('calling refund', () => {
    it('fails if caller is not contract canceler', async () => {
      try {
        await Escrow.refund({ from: accounts[1] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if contract status is partial', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });
        const contractStatus = await Escrow.getStatus.call();
        assert.equal(contractStatus.toNumber(), 2);
        await Escrow.refund({ from: accounts[0] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if contract status is paid', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        await Escrow.payOut(100, accounts[3], url, hash, { from: reputationOracle });
        const contractStatus = await Escrow.getStatus.call();
        assert.equal(contractStatus.toNumber(), 3);
        await Escrow.refund({ from: accounts[0] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('transfers all tokens back to canceler', async () => {
      try {
        const initialAccountBalance = await Escrow.getAddressBalance.call(accounts[0]);
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        await Escrow.refund({ from: accounts[0] });
        const accountBalance = await Escrow.getAddressBalance.call(accounts[0]);
        assert.equal(accountBalance.toNumber(), initialAccountBalance.toNumber());
      } catch (ex) {
        assert(false);
      }
    });

    it('sets status to canceled if succesful', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        await Escrow.refund({ from: accounts[0] });
        const contractStatus = await Escrow.getStatus.call();
        assert.equal(contractStatus, 5);
      } catch (ex) {
        assert(false);
      }
    });

    it('fails if contract status is complete', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        await Escrow.payOut(100, accounts[3], url, hash, { from: reputationOracle });
        await Escrow.complete({ from: reputationOracle });
        const contractStatus = await Escrow.getStatus.call();
        assert.equal(contractStatus.toNumber(), 4);
        await Escrow.refund({ from: accounts[0] });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('succesfully pays recipient', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });
        const recipientBalance = await Escrow.getAddressBalance.call(accounts[3]);
        assert.equal(recipientBalance.toNumber(), 10);
      } catch (ex) {
        assert(false);
      }
    });

    it('sets contract status to partial if contract has money left after payout', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });
        const contractStatus = await Escrow.getStatus.call();
        assert.equal(contractStatus.toNumber(), 2);
      } catch (ex) {
        assert(false);
      }
    });

    it('sets contract status to paid after paying recipient all contract balance', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
        await Escrow.payOut(100, accounts[3], url, hash, { from: reputationOracle });
        const contractStatus = await Escrow.getStatus.call();
        assert.equal(contractStatus.toNumber(), 3);
      } catch (ex) {
        assert(false);
      }
    });

    it('stores payout url and hash', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 0, url, hash, { from: accounts[0] });
        await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });
        const fUrl = await Escrow.getFUrl.call();
        const fHash = await Escrow.getFHash.call();
        assert.equal(fUrl, url);
        assert.equal(fHash, hash);
      } catch (ex) {
        assert(false);
      }
    });

    it('fails if contract balance is zero', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, 0, url, hash, { from: accounts[0] });
        await Escrow.payOut(10, accounts[1], url, hash, { from: reputationOracle });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('succesfully pays fees to oracles', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, 10, url, hash, { from: accounts[0] });

        const initialReputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);
        const initialRecordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);

        await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });

        const reputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);
        const recordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);

        const amountOfPaidToReputationOracle = reputationOracleBalance.toNumber() - initialReputationOracleBalance.toNumber();
        const amountOfPaidToRecordingOracle = recordingOracleBalance.toNumber() - initialRecordingOracleBalance.toNumber();
        assert.equal(amountOfPaidToRecordingOracle, 1);
        assert.equal(amountOfPaidToReputationOracle, 1);
        assert.equal(amountOfPaidToRecordingOracle, amountOfPaidToReputationOracle);
      } catch (ex) {
        assert(false);
      }
    });

    it('pays both oracles the same amount', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, 10, url, hash, { from: accounts[0] });

        const initialReputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);
        const initialRecordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);

        await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });

        const reputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);
        const recordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);

        const amountOfPaidToReputationOracle = reputationOracleBalance.toNumber() - initialReputationOracleBalance.toNumber();
        const amountOfPaidToRecordingOracle = recordingOracleBalance.toNumber() - initialRecordingOracleBalance.toNumber();
        assert.equal(amountOfPaidToRecordingOracle, amountOfPaidToReputationOracle);
      } catch (ex) {
        assert(false);
      }
    });
  });

  describe('calling bulkPayOut', () => {
    it('pays each recipient their corresponding amount', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, 0, url, hash, { from: accounts[0] });
        const initialAccount3Balance = await Escrow.getAddressBalance.call(accounts[3]);
        const initialAccount4Balance = await Escrow.getAddressBalance.call(accounts[4]);
        const initialAccount5Balance = await Escrow.getAddressBalance.call(accounts[5]);

        await Escrow.bulkPayOut([accounts[3], accounts[4], accounts[5]], [10, 20, 30], url, hash, '000', { from: reputationOracle });

        const account3Balance = await Escrow.getAddressBalance.call(accounts[3]);
        const account4Balance = await Escrow.getAddressBalance.call(accounts[4]);
        const account5Balance = await Escrow.getAddressBalance.call(accounts[5]);

        const amountOfPaidToAccountThree = account3Balance.toNumber() - initialAccount3Balance.toNumber();
        const amountOfPaidToAccountFour = account4Balance.toNumber() - initialAccount4Balance.toNumber();
        const amountOfPaidToAccountFive = account5Balance.toNumber() - initialAccount5Balance.toNumber();

        assert.equal(amountOfPaidToAccountThree, 8);
        assert.equal(amountOfPaidToAccountFour, 16);
        assert.equal(amountOfPaidToAccountFive, 24);
      } catch (ex) {
        assert(false);
      }
    });

    it('pays oracles their fees', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, 0, url, hash, { from: accounts[0] });
        const initialRecordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);
        const initialReputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);

        await Escrow.bulkPayOut([accounts[3], accounts[4], accounts[5]], [10, 20, 30], url, hash, '000', { from: reputationOracle });

        const recordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);
        const reputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);

        const amountOfPaidToRecordingOracle = recordingOracleBalance.toNumber() - initialRecordingOracleBalance.toNumber();
        const amountOfPaidToReputationOracle = reputationOracleBalance.toNumber() - initialReputationOracleBalance.toNumber();

        assert.equal(amountOfPaidToRecordingOracle, 6);
        assert.equal(amountOfPaidToReputationOracle, 6);
      } catch (ex) {
        assert(false);
      }
    });
  });

  it('runs from setup to bulkPayOut to complete correctly', async () => {
    try {
      const toAddress = [accounts[0]];
      const initialStatus = await Escrow.getStatus.call();
      assert.equal(initialStatus, 0);

      // Transer funds to escrow
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });

      // Setup escrow
      await Escrow.setup(reputationOracle, recordingOracle, 10, 10, 0, url, hash, { from: accounts[0] });
      const setupStatus = await Escrow.getStatus.call();
      assert.equal(setupStatus, 1);

      const amountToPay = [100];
      await Escrow.bulkPayOut(toAddress, amountToPay, url, hash, '000', { from: reputationOracle });
      const paidStatus = await Escrow.getStatus.call();
      assert.equal(paidStatus, 3);

      // Complete escrow
      await Escrow.complete({ from: reputationOracle });
      const completeStatus = await Escrow.getStatus.call();
      assert.equal(completeStatus, 4);
    } catch (ex) {
      assert(false);
    }
  });

  it('runs from setup to bulkPayOut to complete correctly with multiple addresses', async () => {
    try {
      const toAddresses = [accounts[0], accounts[1]];
      const initialStatus = await Escrow.getStatus.call();
      assert.equal(initialStatus, 0);

      // Transer funds to escrow
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });

      // Setup escrow
      await Escrow.setup(reputationOracle, recordingOracle, 10, 10, 0, url, hash, { from: accounts[0] });
      const setupStatus = await Escrow.getStatus.call();
      assert.equal(setupStatus, 1);

      const amountsToPay = [50, 50];
      await Escrow.bulkPayOut(toAddresses, amountsToPay, url, hash, '000', { from: reputationOracle });
      const paidStatus = await Escrow.getStatus.call();
      assert.equal(paidStatus, 3);

      // Complete escrow
      await Escrow.complete({ from: reputationOracle });
      const completeStatus = await Escrow.getStatus.call();
      assert.equal(completeStatus, 4);
    } catch (ex) {
      assert(false);
    }
  });

  it('runs from setup to payout to complete correctly', async () => {
    try {
      const toAddress = accounts[1];
      const initialStatus = await Escrow.getStatus.call();
      assert.equal(initialStatus, 0);

      // Transer funds to escrow
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });

      // Setup escrow
      await Escrow.setup(reputationOracle, recordingOracle, 10, 10, 0, url, hash, { from: accounts[0] });
      const setupStatus = await Escrow.getStatus.call();
      assert.equal(setupStatus, 1);

      // Pay out partial amount of contract funds
      const amountToPay = 1;
      await Escrow.payOut(amountToPay, toAddress, url, hash, { from: reputationOracle });
      const partialStatus = await Escrow.getStatus.call();
      assert.equal(partialStatus, 2);

      // Pay out all funds contract has left
      const amountToPay2 = 99;
      await Escrow.payOut(amountToPay2, toAddress, url, hash, { from: reputationOracle });
      const paidStatus = await Escrow.getStatus.call();
      assert.equal(paidStatus, 3);

      // Complete escrow
      await Escrow.complete({ from: reputationOracle });
      const completeStatus = await Escrow.getStatus.call();
      assert.equal(completeStatus, 4);
    } catch (ex) {
      assert(false);
    }
  });
});
