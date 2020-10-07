require('dotenv').config()
const bodyParser = require('body-parser');
const express = require('express');

const app = express();

const ETHInterface = require('./ETHInterface')
const Job = require('./Job')

const port = process.env.PORT || 8080;

//body-parser middleware
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());

app.get('/factory/:factoryId', async (req, res) => {
  const factoryId = req.params.factoryId
  try { 
    const transactions = await ETHInterface.list_transactions(factoryId)
    return res.json(transactions)
  }
  catch(e) {
    console.log(e)
    return res.status(500).send({error: "Something went wrong"})
  }
})

app.get('/escrows/:escrowId', async (req, res) => {
  const escrowId = req.params.escrowId
  try {
    const manifest_url = await ETHInterface.get_escrow(escrowId).methods.manifestUrl().call()
    return res.send({url: manifest_url})
  }
  catch(e) { 
    console.log(e)
    return res.status(500).send({error: "Something went wrong"})
  }
})

app.post('/job', (req, res) => {
  const gas_payer = req.body.gas_payer
  const gas_payer_priv = req.body.gas_payer_priv
  const rep_oracle_pub_key = req.body.rep_oracle_pub_key
  const manifest_url = req.body.manifest_url

  try {
    const job = new Job(gas_payer, 
                        gas_payer_priv, 
                        rep_oracle_pub_key, 
                        manifest_url)
    job.launch()
    res.send({message: "Pending Verification & Upload"})
  }
  catch(e) { 
    console.log(e)
    return res.status(500).send({error: "Something went wrong"})
  }
})

app.listen(port, () => console.log(`Server Started at port ${port}`));
