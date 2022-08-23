// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.6.2;
/**
 * @title SKALEStorage
 * @dev Create, kill & retrieve code of contract
 */
contract SkaleStorage {
    // struct to save creation blockNumber and removing blockNumber
    struct BlockData {
        uint256 blockStarted;
        uint256 blockFinished;
    }
    // mapping contract => BlockData - save contract states
    mapping(address => BlockData) private _contractLife;
    /**
     * @dev stores that contract was created
     * @param contractAddress - address of contract
     *
     * contract should not be already created
     * contract should not be already killed
     */
    function create(address contractAddress) public {
        require(_contractLife[contractAddress].blockStarted == 0, "Contract was already created");
        require(_contractLife[contractAddress].blockFinished == 0, "Contract was already killed");
        _contractLife[contractAddress].blockStarted = block.number;
    }
    /**
     * @dev stores that contract was killed
     * @param contractAddress - address of contract
     *
     * contract should be created
     * contract should be created before kill
     * contract should not be already killed
     */
    function kill(address contractAddress) public {
        require(_contractLife[contractAddress].blockStarted != 0, "Contract was not created");
        require(_contractLife[contractAddress].blockStarted <= block.number, "Contract will create after it killed");
        require(_contractLife[contractAddress].blockFinished == 0, "Contract was already killed");
        _contractLife[contractAddress].blockFinished = block.number;
    }

    function getBlockNumber(address contractAddress) public view returns(uint256 blockNumber){
        return _contractLife[contractAddress].blockStarted;
    }

    /**
     * @dev returns code if exists
     * @param contractAddress - address of contract
     * @param blockNumber - number of block
     */
    function getCode(address contractAddress, uint256 blockNumber) public view returns(bytes memory codeData) {
        if (_contractLife[contractAddress].blockStarted < blockNumber || _contractLife[contractAddress].blockFinished >= blockNumber) {
            codeData = "";
        }
        assembly {
        // retrieve the size of the code, this needs assembly
            let size := extcodesize(contractAddress)
        // allocate output byte array - this could also be done without assembly
        // by using codeData = new bytes(size)
            codeData := mload(0x40)
        // new "memory end" including padding
            mstore(0x40, add(codeData, and(add(add(size, 0x20), 0x1f), not(0x1f))))
        // store length in memory
            mstore(codeData, size)
        // actually retrieve the code, this needs assembly
            extcodecopy(contractAddress, add(codeData, 0x20), 0, size)
        }
    }
}

