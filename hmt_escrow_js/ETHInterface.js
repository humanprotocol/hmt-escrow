require('dotenv').config()

const EscrowABI= require('./ABIs/Escrow')
const EscrowFactoryABI = require('./ABIs/EscrowFactory')
const HMTTokenInterfaceABI = require('./ABIs/HMTTokenInterface')

const HDWalletProvider = require("truffle-hdwallet-provider")
const web3 = require('web3')
const isUrl = require('is-url')

let HMTOKEN_ADDR = process.env.HMTOKEN_ADDR || "0x4C18A2E51edC5043e9c4B6b0757990A4Ac13797f"

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
  return await this.web3Instance.eth.sendSignedTransaction(signedTransaction.rawTransaction)
  } 

  get_factory(factory_addr) {
    return new this.web3Instance.eth.Contract(EscrowFactoryABI.abi, factory_addr)
  }

  get_escrow(escrow_addr) {
    return new this.web3Instance.eth.Contract(EscrowABI.abi, escrow_addr)
  }

  get_hmt_token() {
    return new this.web3Instance.eth.Contract(HMTTokenInterfaceABI.abi, HMTOKEN_ADDR)
  }

  async init_factory(pub_key, priv_key) {
    const factory = new this.web3Instance.eth.Contract(EscrowFactoryABI.abi)

    try {
      let handle = await this.send_txn(
        factory.deploy({
          data: '0x' + EscrowFactoryABI.bytecode,
          arguments: [HMTOKEN_ADDR]
        }),
        pub_key, 
        priv_key)
      
      return handle.contractAddress
    }
    catch {
      throw new Error("Factory Creation Failled")
    }
    
  }

  async init_escrow(factory_contract, trusted_handlers, pub_key, priv_key) {
    try {
      let handle = await this.send_txn(
        factory_contract.methods.createEscrow(trusted_handlers),
        pub_key,
        priv_key
      )
      return await factory_contract.methods.lastEscrow.call({from: pub_key})
    }
    catch {
      throw new Error("Escrow creation Failed")
    }
  }


  async transfer_hmt(hmt_contract, escrow_addr, hmt_amount, pub_key, priv_key) {
    try {
      let handle = await this.send_txn(
        hmt_contract.methods.transfer(escrow_addr, hmt_amount),
        pub_key,
        priv_key
      )
    }
    catch {
      throw new Error("Failed to deposit HMT")
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
      let handle = await this.send_txn(
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
    catch {
      throw new Error("Failed to Setup Job")
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