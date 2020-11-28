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
    canceler = accounts[0];
    launcher = accounts[1];
    reputationOracle = accounts[2];
    recordingOracle = accounts[3];
    externalAddress = accounts[4];
    trustedHandlers = [reputationOracle, recordingOracle];
    HMT = await HMTokenAbstraction.new('100', 'Human Token', 4, 'HMT', { from: canceler });
    Escrow = await EscrowAbstraction.new(HMT.address, canceler, 5, trustedHandlers, { from: launcher });
  });

  describe('calling eip20', () => {
    it('returns correct token address', async () => {
      try {
        const address = await Escrow.eip20.call();
        assert.equal(address, HMT.address);
      } catch (ex) {
        assert(false);
      }
    });
  });

  describe('initial', () => {
    it('status is launched', async () => {
      try {
        const initialStatus = await Escrow.status.call();
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

    it('launcher returns the contract creator', async () => {
      const launcher_val = await Escrow.launcher.call();
      assert.equal(launcher, launcher_val);
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
        tx = await Escrow.abort({ from: canceler });
        console.log(`Abort costs: ${tx.receipt.gasUsed} wei.`);
        assert(true);
      } catch (ex) {
        assert(false);
      }
    });

    it('fails when aborting with different address', async () => {
      try {
        tx = await Escrow.abort({ from: externalAddress });
        console.log(`Abort costs: ${tx.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('succeeds if caller is a trusted handler', async () => {
      try {
        tx1 = await Escrow.addTrustedHandlers([reputationOracle], { from: launcher });
        console.log(`AddTrustedHandlers costs: ${tx1.receipt.gasUsed} wei.`);
        tx2 = await Escrow.abort({ from: reputationOracle });
        console.log(`Abort costs: ${tx2.receipt.gasUsed} wei.`);
        assert(true);
      } catch (ex) {
        assert(false);
      }
    });
  });

  describe('calling addTrustedHandlers', async () => {
    it('fails if a non-contract creator tries to add trusted handler', async () => {
      try {
        tx1 = await Escrow.addTrustedHandlers([reputationOracle], { from: externalAddress });
        console.log(`AddTrustedHandlers costs: ${tx1.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('succeeds when the contract launcher adds trusted handlers and a trusted handler stores results', async () => {
      try {
        tx1 = await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: launcher });
        console.log(`Setup costs: ${tx1.receipt.gasUsed} wei.`);
        tx2 = await Escrow.addTrustedHandlers([externalAddress], { from: launcher });
        console.log(`AddTrustedHandlers costs: ${tx2.receipt.gasUsed} wei.`);
        tx3 = await Escrow.storeResults(url, hash, { from: externalAddress });
        console.log(`StoreResults costs: ${tx3.receipt.gasUsed} wei.`);
        assert(true);
      } catch (ex) {
        assert(false);
      }
    });

    it('fails if an external address, not a trusted handler stores results', async () => {
      try {
        tx1 = await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx1.receipt.gasUsed} wei.`);
        tx2 = await Escrow.storeResults(url, hash, { from: externalAddress });
        console.log(`StoreResults costs: ${tx2.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });
  });

  describe('calling setup', () => {
    it('fails when calling with different address than the contract was created with', async () => {
      try {
        tx = await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: externalAddress });
        console.log(`Setup costs: ${tx.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if reputation oracle or recording oracle stake is too high', async () => {
      try {
        tx = await Escrow.setup(reputationOracle, recordingOracle, 500, 500, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if reputation oracle or recording oracle stake is too low', async () => {
      try {
        tx = await Escrow.setup(reputationOracle, recordingOracle, 0, 0, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('sets parameters correctly', async () => {
      await HMT.transfer(Escrow.address, 100, { from: canceler });
      tx = await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
      console.log(`Setup costs: ${tx.receipt.gasUsed} wei.`);
      const contractReputationOracle = await Escrow.reputationOracle.call();
      const contractRecordingOracle = await Escrow.recordingOracle.call();
      const contractManifestUrl = await Escrow.manifestUrl.call();
      const contractManifestHash = await Escrow.manifestHash.call();

      assert.equal(contractReputationOracle, reputationOracle);
      assert.equal(contractRecordingOracle, recordingOracle);
      assert.equal(contractManifestUrl, url);
      assert.equal(contractManifestHash, hash);
    });

    it('sets status to pending', async () => {
      await HMT.transfer(Escrow.address, 100, { from: canceler });
      tx = await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
      console.log(`Setup costs: ${tx.receipt.gasUsed} wei.`);
      const status = await Escrow.status.call();
      assert.equal(1, status);
    });
  });

  describe('calling complete', () => {
    it('fails if trying to complete with other than reputation oracle address', async () => {
      try {
        tx = await Escrow.complete({ from: canceler });
        console.log(`Complete costs: ${tx.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if escrow status is not complete or paid', async () => {
      try {
        tx = await Escrow.complete({ from: reputationOracle });
        console.log(`Complete costs: ${tx.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });
  });

  describe('calling storeResults', () => {
    it('fails if calling address is not recording oracle', async () => {
      try {
        tx = await Escrow.storeResults('url', 'hash', { from: canceler });
        console.log(`StoreResults costs: ${tx.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('fails if status is other than pending or partial', async () => {
      try {
        tx1 = await Escrow.setup(reputationOracle, recordingOracle, 1, 1, 0, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx1.receipt.gasUsed} wei.`);
        tx2 = await Escrow.storeResults('url', 'hash', { from: recordingOracle });
        console.log(`StoreResults costs: ${tx2.receipt.gasUsed} wei.`);
        assert(false);

        const totalGas = tx1.receipt.gasUsed + tx2.receipt.gasUsed;
        assert(totalGas <= 500000, `Too much gas used: ${totalGas}. Should have used less than: ${500000}`);
      } catch (ex) {
        assert(true);
      }
    });

    it('succeeds if status is pending', async () => {
      try {
        tx1 = await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx1.receipt.gasUsed} wei.`);
        tx2 = await Escrow.storeResults(url, hash, { from: recordingOracle });
        console.log(`StoreResults costs: ${tx2.receipt.gasUsed} wei.`);
        assert.equal(tx2.logs[0].event, 'IntermediateStorage');
        assert.equal(tx2.logs[0].args._url, url);
        assert.equal(tx2.logs[0].args._hash, hash);
      } catch (ex) {
        assert(false);
      }
    });
  });

  describe('calling cancel', () => {
    it('fails if caller is not contract canceler', async () => {
      try {
        tx = await Escrow.cancel({ from: launcher });
        console.log(`Cancel costs: ${tx.receipt.gasUsed} wei.`);
        assert(false);
      } catch (ex) {
        assert(true);
      }
    });

    it('transfers all tokens back to canceler', async () => {
      try {
        const initialAccountBalance = await Escrow.getAddressBalance.call(canceler);
        await HMT.transfer(Escrow.address, 100, { from: canceler });
        tx1 = await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx1.receipt.gasUsed} wei.`);
        tx2 = await Escrow.cancel({ from: canceler });
        console.log(`Cancel costs: ${tx2.receipt.gasUsed} wei.`);
        const accountBalance = await Escrow.getAddressBalance.call(canceler);
        assert.equal(accountBalance.toNumber(), initialAccountBalance.toNumber());
      } catch (ex) {
        assert(false);
      }
    });

    it('sets status to canceled if succesful', async () => {
      try {
        await HMT.transfer(Escrow.address, 100, { from: canceler });
        tx1 = await Escrow.setup(reputationOracle, recordingOracle, 1, 1, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx1.receipt.gasUsed} wei.`);
        tx2 = await Escrow.cancel({ from: canceler });
        console.log(`Cancel costs: ${tx2.receipt.gasUsed} wei.`);
        const contractStatus = await Escrow.status.call();
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
        tx1 = await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx1.receipt.gasUsed} wei.`);
        const initialAccount3Balance = await Escrow.getAddressBalance.call(accounts[6]);
        const initialAccount4Balance = await Escrow.getAddressBalance.call(accounts[7]);
        const initialAccount5Balance = await Escrow.getAddressBalance.call(accounts[8]);
        const initialRecordingOracleBalance = await Escrow.getAddressBalance.call(recordingOracle);
        const initialReputationOracleBalance = await Escrow.getAddressBalance.call(reputationOracle);

        tx2 = await Escrow.bulkPayOut([accounts[6], accounts[7], accounts[8]], [10, 20, 30], url, hash, '000', { from: reputationOracle });
        console.log(`BulkPayOut costs: ${tx2.receipt.gasUsed} wei.`);

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
        const initialStatus = await Escrow.status.call();
        assert.equal(initialStatus, 0);

        // Transer funds to escrow
        await HMT.transfer(Escrow.address, 100, { from: canceler });

        // Setup escrow
        tx1 = await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx1.receipt.gasUsed} wei.`);
        const setupStatus = await Escrow.status.call();
        assert.equal(setupStatus, 1);

        const amountToPay = [100];
        tx2 = await Escrow.bulkPayOut(toAddress, amountToPay, url, hash, '000', { from: reputationOracle });
        console.log(`BulkPayOut costs: ${tx2.receipt.gasUsed} wei.`);
        const paidStatus = await Escrow.status.call();
        assert.equal(paidStatus, 3);

        // Complete escrow
        tx3 = await Escrow.complete({ from: reputationOracle });
        console.log(`Complete costs: ${tx3.receipt.gasUsed} wei.`);
        const completeStatus = await Escrow.status.call();
        assert.equal(completeStatus, 4);

        const totalGas = tx1.receipt.gasUsed + tx2.receipt.gasUsed + tx3.receipt.gasUsed;
        assert(totalGas <= 1000000, `Too much gas used: ${totalGas}. Should have used less than: ${1000000}`);
      } catch (ex) {
        assert(false);
      }
    });

    it('runs from setup to bulkPayOut to complete correctly with multiple addresses', async () => {
      try {
        const toAddresses = [externalAddress, launcher];
        const initialStatus = await Escrow.status.call();
        assert.equal(initialStatus, 0);

        // Transer funds to escrow
        await HMT.transfer(Escrow.address, 100, { from: canceler });

        // Setup escrow
        tx1 = await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: canceler });
        console.log(`Setup costs: ${tx1.receipt.gasUsed} wei.`);
        const setupStatus = await Escrow.status.call();
        assert.equal(setupStatus, 1);

        const amountsToPay = [50, 50];
        tx2 = await Escrow.bulkPayOut(toAddresses, amountsToPay, url, hash, '000', { from: reputationOracle });
        console.log(`BulkPayOut costs: ${tx2.receipt.gasUsed} wei.`);
        const paidStatus = await Escrow.status.call();
        assert.equal(paidStatus, 3);

        // Complete escrow
        tx3 = await Escrow.complete({ from: reputationOracle });
        console.log(`Complete costs: ${tx3.receipt.gasUsed} wei.`);
        const completeStatus = await Escrow.status.call();
        assert.equal(completeStatus, 4);

        const totalGas = tx1.receipt.gasUsed + tx2.receipt.gasUsed + tx3.receipt.gasUsed;
        assert(totalGas <= 1000000, `Too much gas used: ${totalGas}. Should have used less than: ${1000000}`);
      } catch (ex) {
        assert(false);
      }
    });
  });
});
