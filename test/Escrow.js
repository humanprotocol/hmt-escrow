const EscrowAbstraction = artifacts.require('Escrow');
const HMTokenAbstraction = artifacts.require('HMToken');

let Escrow;
let HMT;
let reputationOracle;
let recordingOracle;
const url = 'http://google.com/fake';
const hash = 'fakehash';

const txShouldFail = e => assert('tx' in e && e.tx !== undefined, JSON.stringify(e)); 

contract('Escrow', (accounts) => {
  beforeEach(async () => {
    HMT = await HMTokenAbstraction.new('100', 'Human Token', 4, 'HMT', { from: accounts[0] });
    reputationOracle = accounts[1];
    recordingOracle = accounts[2];

    Escrow = await EscrowAbstraction.new(HMT.address, accounts[0], 5, { from: accounts[0] });
  });

  describe('calling getTokenAddress', () => {
    it('returns correct token address', async () => {
      const address = await Escrow.getTokenAddress.call();
      assert.equal(address, HMT.address);
    });
  });

  describe('initial', () => {
    it('status is launched', async () => {
      const initialStatus = await Escrow.getStatus.call();
      assert.equal(0, initialStatus);
    });

    it('balance is 0', async () => {
      const initialBalance = await Escrow.getBalance.call();
      assert.equal(initialBalance.toNumber(), 0);
    });

    it('launcher is 0', async () => {
        const launcher = await Escrow.getLauncher.call();
        assert.equal(launcher, '0x1413862C2B7054CDbfdc181B83962CB0FC11fD92');
    });

    it('transfering money to escrow increases balance', async () => {
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      const balance = await Escrow.getBalance.call();
      assert.equal(balance.toNumber(), 100);
    });
  });

  describe('calling abort', () => {
    it('succeeds when aborting with same address', async () => {
      await Escrow.abort({ from: accounts[0] });
    });

    it('fails when aborting with different address', async () => {
      await Escrow.abort({ from: accounts[1] }).catch(txShouldFail);
    });
  });

  describe('calling setup', () => {
    it('fails when calling with different address than the contract was created with', async () => {
      await Escrow.setup(reputationOracle, recordingOracle, 1, 10, url, hash, { from: accounts[1] }).catch(txShouldFail);
    });

    it('fails if reputation oracle or recording oracle stake is too high', async () => {
      await Escrow.setup(reputationOracle, recordingOracle, 500, 500, url, hash, { from: accounts[1] }).catch(txShouldFail);
    });

    it('fails if reputation oracle or recording oracle stake is too low', async () => {
      await Escrow.setup(reputationOracle, recordingOracle, 0, 0, url, hash, { from: accounts[1] }).catch(txShouldFail);
    });

    it('fails if contract has sufficient funds', async () => {
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: accounts[0] }).catch(txShouldFail);
    });

    it('sets parameters correctly', async () => {
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: accounts[0] });
      const contractReputationOracle = await Escrow.getReputationOracle.call();
      const contractRecordingOracle = await Escrow.getRecordingOracle.call();
      const contractManifestUrl = await Escrow.getManifestUrl.call();
      const contractManifestHash = await Escrow.getManifestHash.call();

      assert.equal(contractReputationOracle, reputationOracle);
      assert.equal(contractRecordingOracle, recordingOracle);
      assert.equal(contractManifestUrl, url);
      assert.equal(contractManifestHash, hash);
    });

    it('sets status to pending', async () => {
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: accounts[0] });
      const status = await Escrow.getStatus.call();
      assert.equal(1, status);
    });
  });

  describe('calling complete', () => {
    it('fails if trying to complete with other than reputation oracle address', async () => {
      await Escrow.complete({ from: accounts[0] }).catch(txShouldFail);
    });

    it('fails if escrow status is not complete or paid', async () => {
      await Escrow.complete({ from: reputationOracle }).catch(txShouldFail);
    });
  });

  describe('calling storeResults', () => {
    it('fails if calling address is not recording oracle', async () => {
      await Escrow.storeResults('url', 'hash', { from: accounts[0] }).catch(txShouldFail);
    });

    it('fails if status is other than pending or partial', async () => {
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: accounts[0] });
      await Escrow.storeResults('url', 'hash', { from: accounts[2] }).catch(txShouldFail);
    });

    it('succeeds if status is pending', async () => {
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: accounts[0] });
      await Escrow.storeResults(url, hash, { from: accounts[2] });
      const IntermediateResultsUrl = await Escrow.getIntermediateResultsUrl.call();
      const IntermediateResultsHash = await Escrow.getIntermediateResultsHash.call();
      assert.equal(IntermediateResultsUrl, url);
      assert.equal(IntermediateResultsHash, hash);
    });
  });

  describe('calling cancel', () => {
    it('fails if caller is not contract canceler', async () => {
      await Escrow.cancel({ from: accounts[1] }).catch(txShouldFail);
    });

    it('transfers all tokens back to canceler', async () => {
      const initialAccountBalance = await Escrow.getAddressBalance.call(accounts[0]);
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: accounts[0] });
      await Escrow.cancel({ from: accounts[0] });
      const accountBalance = await Escrow.getAddressBalance.call(accounts[0]);
      assert.equal(accountBalance.toNumber(), initialAccountBalance.toNumber());
    });

    it('sets status to canceled if succesful', async () => {
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: accounts[0] });
      await Escrow.cancel({ from: accounts[0] });
      const contractStatus = await Escrow.getStatus.call();
      assert.equal(contractStatus, 5);
    });
  });

  describe('calling bulkPayOut', () => {
    it('pays each recipient their corresponding amount', async () => {
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: accounts[0] });
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
    });

    it('pays oracles their fees', async () => {
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: accounts[0] });
      const initialRecordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);
      const initialReputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);

      await Escrow.bulkPayOut([accounts[3], accounts[4], accounts[5]], [10, 20, 30], url, hash, '000', { from: reputationOracle });
      
      const recordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);
      const reputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);
      
      const amountOfPaidToRecordingOracle = recordingOracleBalance.toNumber() - initialRecordingOracleBalance.toNumber();
      const amountOfPaidToReputationOracle = reputationOracleBalance.toNumber() - initialReputationOracleBalance.toNumber();
      
      assert.equal(amountOfPaidToRecordingOracle, 6);
      assert.equal(amountOfPaidToReputationOracle, 6);
    });

    it('runs from setup to bulkPayOut to complete correctly', async () => {
      const toAddress = [accounts[0]];
      const initialStatus = await Escrow.getStatus.call();
      assert.equal(initialStatus, 0);

      // Transer funds to escrow
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
      
      // Setup escrow
      await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: accounts[0] });
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
    });

    it('runs from setup to bulkPayOut to complete correctly with multiple addresses', async () => {
      const toAddresses = [accounts[0], accounts[1]];
      const initialStatus = await Escrow.getStatus.call();
      assert.equal(initialStatus, 0);

      // Transer funds to escrow
      await HMT.transfer(Escrow.address, 100, { from: accounts[0] });

      // Setup escrow
      await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: accounts[0] });
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
    });
  });
});
