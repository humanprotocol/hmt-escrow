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
    canceler = accounts[0]
    launcher = accounts[1]
    reputationOracle = accounts[2];
    recordingOracle = accounts[3];
    externalAddress = accounts[4]
    HMT = await HMTokenAbstraction.new('100', 'Human Token', 4, 'HMT', { from: canceler });
    Escrow = await EscrowAbstraction.new(HMT.address, canceler, 5, { from: launcher });
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

    it('launcher is 0', async () => {
      const launcher = await Escrow.getLauncher.call();
      assert.equal(launcher, '0x61F9F0B31eacB420553da8BCC59DC617279731Ac');
    });


    it('transfering money to escrow increases balance', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: canceler });
        const balance = await Escrow.getBalance.call();
        assert.equal(balance.toNumber(), 100);
      } catch (ex) {
        assert(false);
      }
    });
  });

  describe('calling abort', () => {
    it('succeeds when aborting with same address', async () => {
      try {
        await Escrow.abort({ from: canceler });
        assert(true);
      } catch (ex) {
        assert(false);
      }
    });

    it('fails when aborting with different address', async () => {
      try {
        await Escrow.abort({ from: externalAddress });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('succeeds if caller is a trusted handler', async () => {
      try {
        await Escrow.addTrustedHandlers([reputationOracle])
        await Escrow.abort({ from: reputationOracle });
        assert(true);
      } catch (ex) {
        assert(false);
      }
    })
  });

  describe('calling addTrustedHandlers', async () => {
    it('succeeds when the contract launcher adds trusted handlers and a trusted handler stores results', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: canceler });
        await Escrow.addTrustedHandlers([externalAddress], { from: canceler });
        await Escrow.storeResults(url, hash, { from: externalAddress });
        assert(true);
      } catch (ex) {
        assert(false);
      }
    })

    it('fails if an external address, not a trusted handler stores results', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: canceler });
        await Escrow.storeResults(url, hash, { from: externalAddress });
        assert(false)
      } catch (ex) {
        assert(true);
      }
    })
  })

  describe('calling setup', () => {
    it('fails when calling with different address than the contract was created with', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: externalAddress });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if reputation oracle or recording oracle stake is too high', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 500, 500, url, hash, { from: canceler });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if reputation oracle or recording oracle stake is too low', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 0, 0, url, hash, { from: canceler });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('sets parameters correctly', async () => {
      await HMT.transfer(Escrow.address, 100, { from: canceler });
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
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
      await HMT.transfer(Escrow.address, 100, { from: canceler });
      await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
      const status = await Escrow.getStatus.call();
      assert.equal(1, status);
    });
  });

  describe('calling complete', () => {
    it('fails if trying to complete with other than reputation oracle address', async () => {
      try {
        await Escrow.complete({ from: canceler });
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
        await Escrow.storeResults('url', 'hash', { from: canceler });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if status is other than pending or partial', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 0, url, hash, { from: canceler });
        await Escrow.storeResults('url', 'hash', { from: recordingOracle });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('succeeds if status is pending', async () => {
      try {
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
        await Escrow.storeResults(url, hash, { from: recordingOracle });
        const IntermediateResultsUrl = await Escrow.getIntermediateResultsUrl.call();
        const IntermediateResultsHash = await Escrow.getIntermediateResultsHash.call();
        assert.equal(IntermediateResultsUrl, url);
        assert.equal(IntermediateResultsHash, hash);
      } catch (ex) {
        assert(false);
      }
    });
  });

  describe('calling cancel', () => {
    it('fails if caller is not contract canceler', async () => {
      try {
        await Escrow.cancel({ from: launcher });
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('transfers all tokens back to canceler', async () => {
      try {
        const initialAccountBalance = await Escrow.getAddressBalance.call(canceler);
        await HMT.transfer(Escrow.address, 100, { from: canceler });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
        await Escrow.cancel({ from: canceler });
        const accountBalance = await Escrow.getAddressBalance.call(canceler);
        assert.equal(accountBalance.toNumber(), initialAccountBalance.toNumber());
      } catch (ex) {
        assert(false);
      }
    });

    it('sets status to canceled if succesful', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: canceler });
        await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
        await Escrow.cancel({ from: canceler });
        const contractStatus = await Escrow.getStatus.call();
        assert.equal(contractStatus, 5);
      } catch (ex) {
        assert(false);
      }
    });
  });

  describe('calling bulkPayOut', () => {
    it('pays each recipient their corresponding amount', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: canceler });
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: canceler });
        const initialAccount3Balance = await Escrow.getAddressBalance.call(accounts[6]);
        const initialAccount4Balance = await Escrow.getAddressBalance.call(accounts[7]);
        const initialAccount5Balance = await Escrow.getAddressBalance.call(accounts[8]);
        const initialRecordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);
        const initialReputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);

        await Escrow.bulkPayOut([accounts[6], accounts[7], accounts[8]], [10, 20, 30], url, hash, '000', { from: reputationOracle });

        const account3Balance = await Escrow.getAddressBalance.call(accounts[6]);
        const account4Balance = await Escrow.getAddressBalance.call(accounts[7]);
        const account5Balance = await Escrow.getAddressBalance.call(accounts[8]);
        const recordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);
        const reputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);

        const amountOfPaidToAccountThree = account3Balance.toNumber() - initialAccount3Balance.toNumber();
        const amountOfPaidToAccountFour = account4Balance.toNumber() - initialAccount4Balance.toNumber();
        const amountOfPaidToAccountFive = account5Balance.toNumber() - initialAccount5Balance.toNumber();
        const amountOfPaidToRecordingOracle = recordingOracleBalance.toNumber() - initialRecordingOracleBalance.toNumber();
        const amountOfPaidToReputationOracle = reputationOracleBalance.toNumber() - initialReputationOracleBalance.toNumber();

        assert.equal(amountOfPaidToAccountThree, 8);
        assert.equal(amountOfPaidToAccountFour, 16);
        assert.equal(amountOfPaidToAccountFive, 24);
        assert.equal(amountOfPaidToRecordingOracle, 6);
        assert.equal(amountOfPaidToReputationOracle, 6);
      } catch (ex) {
        assert(false);
      }
    });

    it('runs from setup to bulkPayOut to complete correctly', async () => {
      try {
        const toAddress = [externalAddress];
        const initialStatus = await Escrow.getStatus.call();
        assert.equal(initialStatus, 0);

        // Transer funds to escrow
        await HMT.transfer(Escrow.address, 100, { from: canceler });

        // Setup escrow
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: canceler });
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
        const toAddresses = [externalAddress, launcher];
        const initialStatus = await Escrow.getStatus.call();
        assert.equal(initialStatus, 0);

        // Transer funds to escrow
        await HMT.transfer(Escrow.address, 100, { from: canceler });

        // Setup escrow
        await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: canceler });
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
  });
});
