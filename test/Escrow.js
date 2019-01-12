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

  it('returns correct token address', async () => {
    const address = await Escrow.getTokenAddress.call();
    assert.equal(address, HMT.address);
  });

  it('initial status is launched', async () => {
    const initialStatus = await Escrow.getStatus.call();
    assert.equal(0, initialStatus);
  });

  it('initial balance is 0', async () => {
    const initialBalance = await Escrow.getBalance.call();
    assert.equal(initialBalance.toNumber(), 0);
  });

  it('transfering money to escrow increases balance', async () => {
    await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
    const balance = await Escrow.getBalance.call();
    assert.equal(balance.toNumber(), 100);
  });

  it('aborting succeeds when aborting with same address', async () => {
    try {
      await Escrow.abort({ from: accounts[0] });
      assert(true);
    } catch (ex) {
      assert(false);
    }
  });

  it('aborting fails when aborting with different address', async () => {
    try {
      await Escrow.abort({ from: accounts[1] });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('fails to setup with different address than the contract was created with', async () => {
    try {
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[1] });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('fails to setup if reputation oracle or recording oracle stake is too high', async () => {
    try {
      await Escrow.setup(reputationOracle, recordingOracle, 500, 500, 10, url, hash, { from: accounts[1] });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('fails to setup if reputation oracle or recording oracle stake is too low', async () => {
    try {
      await Escrow.setup(reputationOracle, recordingOracle, 0, 0, 10, url, hash, { from: accounts[1] });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('fails to setup if contract has sufficient funds', async () => {
    try {
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('sets parameters correctly when calling setup', async () => {
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

  it('sets status to pending when calling setup', async () => {
    await HMT.transfer(Escrow.address, 100, { from: accounts[0] });
    await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 10, url, hash, { from: accounts[0] });
    const status = await Escrow.getStatus.call();
    assert.equal(1, status);
  });

  it('fails to complete if trying to complete with other than reputation oracle address', async () => {
    try {
      await Escrow.complete({ from: accounts[0] });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('fails to complete if escrow status is not complete or paid', async () => {
    try {
      await Escrow.complete({ from: reputationOracle });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('fails to store results if calling address is not recording oracle', async () => {
    try {
      await Escrow.storeResults('url', 'hash', { from: accounts[0] });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('fails to store results if status is other than pending or partial', async () => {
    try {
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 0, url, hash, { from: accounts[0] });
      await Escrow.storeResults('url', 'hash', { from: accounts[2] });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('can store results when status is pending', async () => {
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

  it('fails to payout if escrow status is not yet setup', async () => {
    try {
      await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });
      assert(false);
    } catch (ex) {
      assert(true);
    }
  });

  it('fails to payout if contract is out ot funds', async () => {
    try {
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 0, url, hash, { from: accounts[0] });
      await Escrow.payOut(10, accounts[3], url, hash, { from: reputationOracle });
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

  it('sets status to partial if contract has money left after payout', async () => {
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

  it('sets status to paid after paying recipient all contract balance', async () => {
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

  it('sets status to complete when calling complete after having paid', async () => {
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

  it('fails to payout if contract balance is zero', async () => {
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

  it('oracles get paid the same amount', async () => {
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

  it('payout stores payout url and hash', async () => {
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

  it('bulkPayOut pays each recipient their corresponding amount', async () => {
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
      console.log(ex);
      assert(false);
    }
  });

  it('bulkPayOut pays oracles their fees', async () => {
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
      console.log(ex);
      assert(false);
    }
  });
});
