const path = require('path')
const fs = require('fs')
const solc = require('solc')

class Contracts {
  constructor(contractPath='../contracts') {
    const contractsPath = path.resolve(__dirname, contractPath)
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
    const contractFile = `${ contractName }.sol`;
    return this._compiledContracts.contracts[contractFile][contractName];
  }

  get_contract_abi(contractName) {
    // Can add error checks here in future, assuming internal now so..
    const contractFile = `${ contractName }.sol`;
    return this._compiledContracts.contracts[contractFile][contractName].abi;
  }

  get_contract_bytecode(contractName) {
    // Can add error checks here in future, assuming internal now so..
    const contractFile = `${ contractName }.sol`;
    return this._compiledContracts.contracts[contractFile][contractName].evm.bytecode.object;
  }

  dump_all(destinationPrefix) {
    // saves all the contacts in json form to disk
    const contractFiles = Object.keys(this._compiledContracts.contracts);

    fs.mkdirSync(destinationPrefix);

    for(var contractFile of contractFiles) {
      console.log(`dumping contract:`, contractFile);
      const name = Object.keys(this._compiledContracts.contracts[contractFile])[0];
      const obj = this.get_contract_abi(name);

      fs.writeFileSync(`./${destinationPrefix}/${name}.json`, JSON.stringify(obj, null, 2));
    }
  }
}

module.exports = new Contracts()
