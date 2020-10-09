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
yarn install @hcaptcha/hmt-escrow-js@1.0.0-alpha.5

# Using NPM
npm yarn install --save @hcaptcha/hmt-escrow-js@1.0.0-alpha.5
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

# Deploying this lib

Right now we have auto deployments disabled while we're in a test phase, until we have testing, better docs, etc.

To do this manually, go into the root `.travis.yaml` file and uncomment:

```yaml
  # on:
  #   branch: npm-publish-js
```

And specify your branch name.  We will make this better in the near future when we have tests in this repo and can bump versions in both python and js to the same version based on the git tag.


# Contributing / Development

### Generating JSON schema from basemodels

```python
from basemodels.pydantic.manifest import Manifest
js_model = Manifest.schema_json(indent=2)
with open('manifest-schema-pydantic.json', 'w', encoding='utf-8') as f:
    json.dump(js_model, f, ensure_ascii=False)
```
