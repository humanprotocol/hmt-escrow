pragma solidity 0.4.24;
import "./Escrow.sol";

contract EscrowFactory {
    uint private counter;
    mapping(address => uint) private escrowCounters;
    address private lastEscrow;
    address private eip20;
    event Launched(address eip20, address escrow);

    constructor(address _eip20) public {
        eip20 = _eip20;
    }

    function createEscrow() public returns (address) {
        Escrow escrow = new Escrow(eip20, msg.sender, 8640000);
        counter++;
        escrowCounters[address(escrow)] = counter;
        lastEscrow = address(escrow);
        emit Launched(eip20, lastEscrow);
    }

    function getCounter() public view returns (uint) {
        return counter;
    }

    function getLastEscrow() public view returns (address) {
        return lastEscrow;
    }

    function getEscrowCounter(address _address) public view returns (uint) {
        uint escrowCounter = escrowCounters[_address];
        return escrowCounter;
    }

    function getEIP20() public view returns (address) {
        return eip20;
    }

    function isChild(address _child) public view returns (bool) {
        return getEscrowCounter(_child) == getCounter();
    }

    function hasEscrow(address _address) public view returns (bool) {
        uint escrowCounter = getEscrowCounter(_address);
        return escrowCounter > 0;
    }
}
