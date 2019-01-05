pragma solidity 0.4.24;
import "./Escrow.sol";
contract EscrowFactory {
    uint private counter;
    address private lastAddress;
    address private eip20;
    event Launched(address eip20, address escrow);

    constructor(address _eip20) public {
        eip20 = _eip20;
    }

    function createEscrow() public returns (address) {
        Escrow escrow = new Escrow(eip20, msg.sender, 8640000);
        ++counter;
        lastAddress = address(escrow);
        emit Launched(eip20, lastAddress);
        return lastAddress;
    }

    function getCounter() public view returns (uint) {
        return counter;
    }

    function getLastAddress() public view returns (address) {
        return lastAddress;
    }

    function getEIP20() public view returns (address) {
        return eip20;
    }

    function isChild(address child) public view returns (bool) {
        return getLastAddress() == child;
    }
}
