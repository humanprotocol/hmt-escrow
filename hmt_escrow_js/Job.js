require('dotenv').config()

const keythereum = require("keythereum")
const ETHInterface = require('./ETHInterface')
const Ajv = require('ajv')
const manifestSchema = require('./manifest-schema-pydantic')
const request = require('request');

class Job {
  constructor(gas_payer, gas_payer_priv, rep_oracle_pub_key, manifest_url, factory_addr=null) {
    this._gas_payer = gas_payer
    this._gas_payer_priv = gas_payer_priv
    this._rep_oracle_pub_key = rep_oracle_pub_key
    this._manifest_url = manifest_url
    this._factory_addr = factory_addr

    this._serialized_manifest = this._download_manifest()
    this.amount = null

    // Validate manifest
    this._validate_manifest()

    if(!this._validate_credentials()) {
      throw Error('Invalid Combination of Public & Private key')
    }

    // Process Manifest
    this._process_manifest()
  }

  _download_manifest() {
    // Download manifest if URL
    // Support for future stuff too like s3, direct upload etc.
    request(this._manifest_url, function (error, response, body) {
      if (!error && response.statusCode == 200) {
        return JSON.parse(body);
      }
      else {
        throw new Error("Couldn't download manifest file, please try again.")
      }
    })
  }


  _validate_credentials() {
    const calculated_pub_key = ETHInterface.web3Instance.utils.toChecksumAddress(keythereum.privateKeyToAddress(this._gas_payer_priv))
    return ETHInterface.web3Instance.utils.toChecksumAddress(this._gas_payer) === calculated_pub_key
  }

  _validate_manifest() {
    const ajv = new Ajv()
    const validate = ajv.compile(manifestSchema)
    if(!validate(this._serialized_manifest)) {
      throw new Error("Manifest invalid")
    }
  }

  _process_manifest() {
    this.amount = Math.round(this._serialized_manifest.task_bid_price * this._serialized_manifest.job_total_tasks)
  }

  
  async launch() {
    // Create Factory if no factory address provided
    if (!this._factory_addr) {
      this._factory_addr = await ETHInterface.init_factory(this._gas_payer, this._gas_payer_priv)
    }

    const factory = await ETHInterface.get_factory(this._factory_addr)

    const trusted_handler = [this._gas_payer]
    // Initialise Escrow, given a particular factory
    const escrow_addr = await ETHInterface.init_escrow(factory, trusted_handler, this._gas_payer, this._gas_payer_priv)
    const escrow = await ETHInterface.get_escrow(escrow_addr)

    // Setup job (eq. job.setup())
    const hmttoken_contract = await ETHInterface.get_hmt_token()

    // Transfer HMT
    await ETHInterface.transfer_hmt(hmttoken_contract, 
                                    escrow_addr,
                                    Math.round(Math.pow(this.amount * 10, 100)),
                                    this._gas_payer, 
                                    this._gas_payer_priv)
    // Setup Job
    await ETHInterface.setup_job(escrow,
                                  this._serialized_manifest.reputation_oracle_addr,
                                  this._serialized_manifest.recording_oracle_addr,
                                  Math.round(this._serialized_manifest.oracle_stake * 100),
                                  Math.round(this._serialized_manifest.oracle_stake * 100),
                                  this._manifest_url,
                                  "",
                                  this._gas_payer,
                                  this._gas_payer_priv)
                               
  }
}

module.exports = Job