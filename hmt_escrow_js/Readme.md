# HMT-Escrow Javascript Module

> This is currently a work in progress port of the escrow library to JS


# Getting started

Setup a `.env` file with following spec and the values you want to deploy with:

```shell
INFURA_KEY=<Fill me in>
MNEMONIC=<Fill me in>
NETWORK="rinkeby"
```

### Install Package

To start using this, you'll need to install it into your project via one of the below methods:

```bash
# with Yarn
yarn install hmt-escrow-js

# Using NPM
npm yarn install --save hmt-escrow-js
```


### Use the module directly to launch new job

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

# Contributing / Development

### Generating JSON schema from basemodels

```python
from basemodels.pydantic.manifest import Manifest
js_model = Manifest.schema_json(indent=2)
with open('manifest-schema-pydantic.json', 'w', encoding='utf-8') as f:
    json.dump(js_model, f, ensure_ascii=False)
```

