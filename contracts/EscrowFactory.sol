pragma solidity 0.6.2;
import "./Escrow.sol";


contract EscrowFactory {
    uint256 private counter;
    mapping(address => uint256) private escrowCounters;
    address private lastEscrow;
    address private eip20;
    event Launched(address eip20, address escrow);

    constructor(address _eip20) public {
        eip20 = _eip20;
    }

    function createEscrow(address[] memory trustedHandlers) public returns (address) {
        Escrow escrow = new Escrow(eip20, msg.sender, 8640000, trustedHandlers);
        counter++;
        escrowCounters[address(escrow)] = counter;
        lastEscrow = address(escrow);
        emit Launched(eip20, lastEscrow);
    }

    function getCounter() public view returns (uint256) {
        return counter;
    }

    function getLastEscrow() public view returns (address) {
        return lastEscrow;
    }

    function getEscrowCounter(address _address) public view returns (uint256) {
        uint256 escrowCounter = escrowCounters[_address];
        return escrowCounter;
    }

    function getEIP20() public view returns (address) {
        return eip20;
    }

    function isChild(address _child) public view returns (bool) {
        return getEscrowCounter(_child) == getCounter();
    }

    function hasEscrow(address _address) public view returns (bool) {
        uint256 escrowCounter = getEscrowCounter(_address);
        return escrowCounter > 0;
    }
}
