// SPDX-License-Identifier: MIT

pragma solidity 0.6.2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
// import "@openzeppelin/contracts/math/SafeMath.sol";
import "./SafeMath.sol";


contract Staking is Ownable{
    using SafeMath for uint256;

    // Info of each user.
    struct UserInfo {
        uint256 amount;
        uint256 lastStakeTime;
        bool validator;
        uint256 voteCount;
        mapping(address => bool) votedAddresses;
    }
    IERC20 public stakingToken;
    address public rewardPool;

    uint256 public apr = 30;                 
    uint256 public totalStaked;             
    uint256 public validatorStakingLimit = 2000;
    uint256 public voteCountLimit = 3;

    mapping (address => UserInfo) public userInfo;  

    event Deposit(address user, uint256 amount);
    event Withdraw(address user, uint256 amount);

    constructor(
        address _token,
        address _rewardPool
    ) public {
        stakingToken = IERC20(_token);
        rewardPool = _rewardPool;
    }

    function updateApr(uint256 _apr) public onlyOwner {
        require(_apr>0, "apr set error");
        apr = _apr;
    }

    function getStakedAmount(address _user) external view returns (uint256) {
        return userInfo[_user].amount;
    }

    function pendingReward(address _user) public view returns (uint256) {
        UserInfo storage user = userInfo[_user];
        uint256 duration = block.timestamp-user.lastStakeTime;
        return user.amount.mul(1e10).mul(apr).mul(duration).div(365 days).div(100);
    }

    function deposit(uint256 _amount) public {
        UserInfo storage user = userInfo[msg.sender];
        
        if (user.amount > 0) {
            uint256 pending = pendingReward(msg.sender);
            if(pending > 0) {
                stakingToken.transferFrom(rewardPool, msg.sender, pending);
            }
        }
        if (_amount > 0) {
            stakingToken.transferFrom(msg.sender, address(this), _amount);
            user.amount = user.amount.add(_amount);
            totalStaked = totalStaked.add(_amount);
            user.lastStakeTime = block.timestamp;
            if (user.amount > validatorStakingLimit){
                user.validator = true;
            }
        }
        
        emit Deposit(msg.sender, _amount);
    }

    function withdraw(uint256 _amount) public {
        UserInfo storage user = userInfo[msg.sender];
        require(user.amount >= _amount, "insufficient");

        uint256 pending = pendingReward(msg.sender);
        if(pending > 0) {
            stakingToken.transferFrom(rewardPool, msg.sender, pending);
        }
        if(_amount > 0) {
            user.amount = user.amount.sub(_amount);
            stakingToken.transfer(msg.sender, _amount);
            totalStaked = totalStaked.sub(_amount);
            if (user.amount <= validatorStakingLimit){
                user.validator = false;
            }

        }
        
        emit Withdraw(msg.sender, _amount);
    }

    function setrewardPool(address _rewardPool) public {
        require(msg.sender == rewardPool, "invalid address");
        require(_rewardPool != address(this), "invalid address");
        require(_rewardPool != address(0), "invalid address");
        rewardPool = _rewardPool;
    }

    function vote_slash(address _user) public {
        UserInfo storage voter = userInfo[msg.sender];
        require(voter.validator, "only validator can vote");
        require(!voter.votedAddresses[_user], "already voted");

        voter.votedAddresses[_user] = true;

        UserInfo storage user = userInfo[_user];
        user.voteCount++;
        
        if(user.voteCount >= voteCountLimit){
            user.amount = 0;
            user.lastStakeTime = 0;
            user.validator = false;
            stakingToken.transfer(rewardPool, user.amount);

        }

        

    }
}