const storage = {};

module.exports = {
  newEscrow: (address) => {
    const escrow = {};
    storage[address] = escrow;

    return escrow;
  },

  getEscrow: (address) => {
    return storage[address];
  },

  getWorkerResult: (escrowAddress, workerAddress) => {
    return storage[escrowAddress][workerAddress];
  },

  putFortune: (escrowAddress, workerAddress, value) => {
    storage[escrowAddress][workerAddress] = value;
  },

  getFortunes: (escrowAddress) => {
    const escrow = storage[escrowAddress];
    const result = [];
    if (!escrow) {
      return result;
    }

    for (let workerAddress of Object.keys(escrow)) {
      result.push({ worker: workerAddress, fortune: escrow[workerAddress] });
    }
    
    return result;
  },

  cleanFortunes: (escrowAddress) => {
    const newEscrow = {};
    storage[escrowAddress] = newEscrow;
  }
}
