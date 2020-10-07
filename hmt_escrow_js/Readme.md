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

To generate pydantic schema,
do:
```python
from basemodels.pydantic.manifest import Manifest
js_model = Manifest.schema_json(indent=2)
with open('manifest-schema-pydantic.json', 'w', encoding='utf-8') as f:
    json.dump(js_model, f, ensure_ascii=False)
```

Use the module directly (launch new job):

```js
  const { Job } = require('hmt_escrow_js')
  try {
    const job = new Job(gas_payer, 
                        gas_payer_priv, 
                        rep_oracle_pub_key, 
                        manifest_url)
    job.launch()
    console.log("Pending Verification & Upload")
  }
  catch(e) { 
    console.log(e)
  }
```
