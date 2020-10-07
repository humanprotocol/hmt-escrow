# HMT-Escrow Javascript Module

Setup a `.env` file with following spec:

```
INFURA_KEY=
MNEMONIC=
NETWORK="rinkeby"
```

Install Dependencies:

```bash
yarn install
```

Either run this as a http-server:
```
npm run start
```

or use the module directly (launch new job):

```js
  const Job = require('./Job')
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
```