// SPDX-License-Identifier: MIT

pragma solidity 0.6.2;
import "./Escrow.sol";
import "./Staking.sol";

contract EscrowFactory {
    // all Escrows will have this duration.
    uint256 constant STANDARD_DURATION = 8640000;
    Staking public stakingContract;
    uint256 public counter;
    mapping(address => uint256) public escrowCounters;
    address public lastEscrow;
    address public eip20;
    // only users that staked over 100 tokens, can create escrow 
    uint256 stakeAmountToEscrow = 100;
    event Launched(address eip20, address escrow);

    constructor(address _eip20, address _sContract) public {
        eip20 = _eip20;
        stakingContract = Staking(_sContract);
    }

    function createEscrow(address[] memory trustedHandlers) public returns (address) {
        //check whether msg.sender staked enough token to create escrow
        uint256 sAmount = stakingContract.getStakedAmount(msg.sender);
        require( sAmount >= stakeAmountToEscrow, "should stake more to create Escrow");
        
        Escrow escrow = new Escrow(eip20, msg.sender, STANDARD_DURATION, trustedHandlers);
        counter++;
        escrowCounters[address(escrow)] = counter;
        lastEscrow = address(escrow);
        emit Launched(eip20, lastEscrow);
        return lastEscrow;
    }

    function isChild(address _child) public view returns (bool) {
        return escrowCounters[_child] == counter;
    }

    function hasEscrow(address _address) public view returns (bool) {
        return escrowCounters[_address] != 0;
    }
}
