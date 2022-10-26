const express = require('express');
const bodyParser = require('body-parser');
const Web3 = require('web3');
const axios = require('axios');
const cors = require('cors');
const storage = require('./storage');
const EscrowFile = require('./build/contracts/Escrow.json');
const EscrowABI = EscrowFile.abi;
const app = express();
const privKey = process.env.ETH_PRIVATE_KEY || '486a0621e595dd7fcbe5608cbbeec8f5a8b5cabe7637f11eccfc7acd408c3a0e'; // ganaches priv key
const ethHttpServer = process.env.ETH_HTTP_SERVER || 'http://localhost:8545';
const port = process.env.PORT || 3005;

const statusesMap = ['Launched', 'Pending', 'Partial', 'Paid', 'Complete', 'Cancelled'];

app.use(bodyParser.json());


const web3 = new Web3(ethHttpServer);
const account = web3.eth.accounts.privateKeyToAccount(`0x${privKey}`);

web3.eth.accounts.wallet.add(account);
web3.eth.defaultAccount = account.address;


app.use(cors());

app.post('/job/results', async function(req, res) {
  try {
    const { workerAddress, escrowAddress, fortune } = req.body;

    if (!web3.utils.isAddress(workerAddress) ) {
      return res.status(400).send({ field: 'workerAddress', message: 'Valid ethereum address required' })
    }
    if (!fortune) {
      return res.status(400).send({ field: 'fortune', message: 'Non-empty fortune is required' });
    }

    if (!web3.utils.isAddress(escrowAddress)) {
      return res.status(400).send({ field: 'escrowAddress', message: 'Valid ethereum address required' })
    }
    const Escrow = new web3.eth.Contract(EscrowABI, escrowAddress);
    const escrowRecOracleAddr = await Escrow.methods.recordingOracle().call({ from: account.address });

    if (web3.utils.toChecksumAddress(escrowRecOracleAddr) !== web3.utils.toChecksumAddress(account.address)) {
      return res.status(400).send({ field: 'escrowAddress', message: 'The Escrow Recording Oracle address mismatches the current one' })
    }

    const escrowStatus = await Escrow.methods.status().call({ from: account.address });

    if (statusesMap[escrowStatus] !== 'Pending') {
      return res.status(400).send({ field: 'escrowAdderss', message: 'The Escrow is not in the Pending status' });
    }

    const manifestUrl = await Escrow.methods.manifestUrl().call({ from: account.address });
    const manifestResponse = await axios.get(convertUrl(manifestUrl));
    const {fortunes_requested: fortunesRequested, reputation_oracle_url: reputationOracleUrl} = manifestResponse.data;

    if (!storage.getEscrow(escrowAddress)) {
      storage.newEscrow(escrowAddress);
    }

    const workerPreviousResult = storage.getWorkerResult(escrowAddress, workerAddress);

    if (workerPreviousResult) {
      return res.status(400).send({ message: `${workerAddress} already submitted a fortune` });
    }

    storage.putFortune(escrowAddress, workerAddress, fortune);
    const fortunes = storage.getFortunes(escrowAddress);

    if (fortunes.length === fortunesRequested) {
      console.log('Doing bulk payouts');
      // a cron job might check how much annotations are in work
      // if this is full - then just push them to the reputation oracle

      await axios.post(convertUrl(reputationOracleUrl), { escrowAddress, fortunes });
      storage.cleanFortunes(escrowAddress);
    }

    res.status(201).send();
  } catch(err) {
    console.log('Error');
    console.error(err);

    res.status(500).send(err);
  }
});

function convertUrl(url){
  return url.replace('localhost', 'host.docker.internal');
}

app.listen(port, () => {
  console.log(`Recording Oracle server listening port ${port}`);
});
