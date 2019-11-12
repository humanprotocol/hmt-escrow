const EscrowAbstraction = artifacts.require('Escrow');
const HMTokenAbstraction = artifacts.require('HMToken');

let Escrow;
let HMT;
let reputationOracle;
let recordingOracle;
const url = 'http://google.com/fake';
const hash = 'fakehash';

const gasReport = [];
let tx;

contract('Escrow', (accounts) => {
  beforeEach(async () => {
    HMT = await HMTokenAbstraction.new('1000', 'Human Token', 4, 'HMT', { from: accounts[0] });
    reputationOracle = accounts[1];
    recordingOracle = accounts[2];

    Escrow = await EscrowAbstraction.new(HMT.address, accounts[0], 5, { from: accounts[0] });
  });

  describe('calling bulkPayOut', () => {
    it('pays each recipient their corresponding amount', async () => {
      await HMT.transfer(Escrow.address, 1000, { from: accounts[0] });
      tx = await Escrow.setup(reputationOracle, recordingOracle, 10, 10, url, hash, { from: accounts[0] });
      gasReport.push(['Setup:', tx.receipt.gasUsed]);
      const recipients = Array(100).fill(accounts[3]);
      const amounts = Array(100).fill(1);
      tx = await Escrow.bulkPayOut(recipients, amounts, url, hash, '000', { from: reputationOracle });
      gasReport.push(['BulkPayout 100 recipients:', tx.receipt.gasUsed]);
    });
  });
  describe('Gas Report', () => {
    it ('', async () => {
      const reportFn = s => console.log('> ', s[0], s[1]);
      console.log('---- GAS REPORT ----');
      gasReport.map(reportFn);
      console.log('---- GAS REPORT ----');
    });
  });
  
});
