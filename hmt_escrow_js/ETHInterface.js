require('dotenv').config()


const HDWalletProvider = require("truffle-hdwallet-provider")
const web3 = require('web3')
const isUrl = require('is-url')

const Contracts = require('./Contracts')

let HMTOKEN_ADDR = process.env.HMTOKEN_ADDR || "0x4dCf5ac4509888714dd43A5cCc46d7ab389D9c23"

class ETHInterface {
  constructor(MNEMONIC, INFURA_KEY, NETWORK) {
    // Setups Required
    if (!MNEMONIC || !INFURA_KEY || !NETWORK ) {
      console.error("Please set a mnemonic, infura key,and network")
      return
    }
    const provider = new HDWalletProvider(MNEMONIC, `https://${NETWORK}.infura.io/v3/${INFURA_KEY}`)
    
    this.web3Instance = new web3(provider)
  }

  async send_txn(txn, pub_key, priv_key) {
    let gas = await txn.estimateGas({from: pub_key})
      let options = {
        from: pub_key,
        data: txn.encodeABI(),
        gas : gas,
        nonce: this.web3Instance.utils.toHex(this.web3Instance.eth.getTransactionCount(pub_key))
      }
    let signedTransaction = await this.web3Instance.eth.accounts.signTransaction(options, priv_key)
    return this.web3Instance.eth.sendSignedTransaction(signedTransaction.rawTransaction)
  } 

  get_factory(factory_addr) {
    return new this.web3Instance.eth.Contract(Contracts.get_contract_abi('EscrowFactory'), factory_addr)
  }

  get_escrow(escrow_addr) {
    return new this.web3Instance.eth.Contract(Contracts.get_contract_abi('Escrow'), escrow_addr)
  }

  get_hmt_token() {
    return new this.web3Instance.eth.Contract(Contracts.get_contract_abi('HMTokenInterface'), HMTOKEN_ADDR)
  }

  async init_factory(pub_key, priv_key) {
    const factory = new this.web3Instance.eth.Contract(Contracts.get_contract_abi('EscrowFactory'))

    try {
      let handle = await this.send_txn(
        factory.deploy({
          data: '0x' + Contracts.get_contract_bytecode('EscrowFactory'),
          arguments: [HMTOKEN_ADDR]
        }),
        pub_key, 
        priv_key)
      
      return handle.contractAddress
    }
    catch (e) {
      throw new Error("Factory creation failled due to: " + e.message)
    }
    
  }

  async init_escrow(factory_contract, trusted_handlers, pub_key, priv_key) {
    try {
      await this.send_txn(
        factory_contract.methods.createEscrow(trusted_handlers),
        pub_key,
        priv_key
      )
      return await factory_contract.methods.lastEscrow.call({from: pub_key})
    }
    catch (e) {
      throw new Error("Escrow creation failed due to: " + e.message)
  }
  }


  async transfer_hmt(hmt_contract, escrow_addr, hmt_amount, pub_key, priv_key) {
    try {
      await this.send_txn(
        hmt_contract.methods.transfer(escrow_addr, hmt_amount),
        pub_key,
        priv_key
      )
    }
    catch (e) {
      throw new Error("Failed to deposit HMT due to: " + e.message)
    }
  }

  async setup_job(escrow_contract, 
                  rep_oracle, 
                  rec_oracle, 
                  rep_oracle_stake, 
                  rec_oracle_stake,  
                  manifest_url,
                  manifest_hash,
                  pub_key,
                  priv_key) {
    try {
        await this.send_txn(
        escrow_contract.methods.setup(rep_oracle,
                                      rec_oracle,
                                      rep_oracle_stake,
                                      rec_oracle_stake,
                                      manifest_url,
                                      manifest_hash),
        pub_key,
        priv_key
      )
    }
    catch (e) {
      throw new Error("Failed to setup job due to: " + e.message)
    }
  }

  async list_transactions(factory_addr) {
      const factory_contract = this.get_factory(factory_addr)
      const events = await factory_contract.getPastEvents('Launched',{                               
        fromBlock: 0,     
        toBlock: 'latest'        
      })

      const transactions = await Promise.all(events.map(event => 
        this.get_escrow(event.returnValues.escrow).methods.manifestUrl().call().
        then(res => (
          { url: res, 
            escrow: event.returnValues.escrow, 
            is_url: isUrl(res)
          })
        )))
      return transactions
  }
}

module.exports = new ETHInterface(
  process.env.MNEMONIC,
  process.env.INFURA_KEY,
  process.env.NETWORK
)