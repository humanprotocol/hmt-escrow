const express = require('express');
const bodyParser = require('body-parser');
const Web3 = require('web3');
const EscrowFile = require('./build/contracts/Escrow.json');
const EscrowABI = EscrowFile.abi;
const { uploadResults } = require('./s3');

const app = express();
const privKey = process.env.ETH_PRIVATE_KEY || '657b6497a355a3982928d5515d48a84870f057c4d16923eb1d104c0afada9aa8';
const ethHttpServer = process.env.ETH_HTTP_SERVER || 'http://localhost:8545';
const port = process.env.PORT || 3006;

const web3 = new Web3(ethHttpServer);
const account = web3.eth.accounts.privateKeyToAccount(`0x${privKey}`);

web3.eth.accounts.wallet.add(account);
web3.eth.defaultAccount = account.address;

app.use(bodyParser.json());

app.post('/job/results', async function(req, res) {
  try {
    const { fortunes, escrowAddress } = req.body;

    if (!Array.isArray(fortunes) || fortunes.length === 0) {
      return res.status(400).send({ message: 'Fortunes are not specified or empty' })
    }

    if (!web3.utils.isAddress(escrowAddress)) {
      return res.status(400).send({ message: 'Escrow address is empty or invalid' });
    }

    const Escrow = new web3.eth.Contract(EscrowABI, escrowAddress);
    const balance = Number(await Escrow.methods.getBalance().call({ from: account.address }));

    const filteredFortunes = filterFortunes(fortunes);
    const evenWorkerReward = calculateRewardForWorker(balance, filteredFortunes.length);
    const resultsUrl = await uploadResults(fortunes.map(({fortune}) => fortune), escrowAddress); 
    // TODO calculate the URL hash(?)
    const resultHash = resultsUrl;
    const workerAddresses = filteredFortunes.map(fortune => fortune.worker).map(web3.utils.toChecksumAddress);
    const rewards = workerAddresses.map(() => evenWorkerReward.toString());
    const bulkTransactionId = 1;

    const gasNeeded = await Escrow.methods.bulkPayOut(workerAddresses, rewards, resultsUrl, resultHash, 1).estimateGas({ from: account.address });
    const gasPrice = await web3.eth.getGasPrice();

    console.log(`bulkpayout will be send, gasNeeded : ${gasNeeded}, gasPrice: ${gasPrice} `);

    await Escrow.methods.bulkPayOut(workerAddresses, rewards, resultsUrl, resultHash, 1).send({ from: account.address, gas: gasNeeded, gasPrice });

    res.status(200).send({ message: 'Escrow has been completed' })
  } catch(err) {
    console.error(err);
    res.status(500).send({ message: err });
  }
});

// leave only unique fortunes
function filterFortunes(addressFortunesEntries) {
  const filteredResults = [];
  const tmpHashMap = {};

  for (let fortuneEntry of addressFortunesEntries) {
    const { fortune } = fortuneEntry;
    if (tmpHashMap[fortune]) {
      continue;
    }

    tmpHashMap[fortune] = true;
    filteredResults.push(fortuneEntry);
  }


  return filteredResults;
}

function calculateRewardForWorker(totalReward, numberOfWorkers) {
  return Math.floor(totalReward / numberOfWorkers);
}

app.listen(port, () => {
  console.log(`Reputation Oracle server listening the port ${port}`);
});
