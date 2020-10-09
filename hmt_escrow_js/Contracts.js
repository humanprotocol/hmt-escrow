const path = require('path')
const fs = require('fs')
const solc = require('solc')

class Contracts {
  constructor(contractFolderPath='../contracts') {
    let contractsPath = null

    contractsPath = path.resolve(__dirname, contractFolderPath)
    if(!fs.existsSync(contractsPath)) {
      // Hack for package
      contractsPath = path.resolve(__dirname, 'contracts')
    }
    const fileNames = fs.readdirSync(contractsPath)

    const contractSources = fileNames.reduce(
      (input, fileName) => {
        const filePath = path.resolve(contractsPath, fileName);
        const source = fs.readFileSync(filePath, "utf-8");
        return { sources: { ...input.sources, [fileName]: {content: source } } };
      },
      { sources: {} },
    )

    const compileInput = {
      language: 'Solidity',
      ...contractSources,
      settings: {
        outputSelection: {
          '*': {
            '*': ['*'],
          },
        },
      }
    }
    this._compiledContracts = JSON.parse(solc.compile(JSON.stringify(compileInput)))
  }

  get_contract_interface(contractName) {
    // Can add error checks here in future, assuming internal now so..
    const contractFile = `${ contractName }.sol`
    return this._compiledContracts.contracts[contractFile][contractName]
  }

  get_contract_abi(contractName) {
    // Can add error checks here in future, assuming internal now so..
    const contractFile = `${ contractName }.sol`
    return this._compiledContracts.contracts[contractFile][contractName].abi
  }

  get_contract_bytecode(contractName) {
    // Can add error checks here in future, assuming internal now so..
    const contractFile = `${ contractName }.sol`
    return this._compiledContracts.contracts[contractFile][contractName].evm.bytecode.object
  }
}

module.exports = new Contracts()
