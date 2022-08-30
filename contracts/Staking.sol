// SPDX-License-Identifier: MIT

pragma solidity 0.6.2;

import "./util/IERC20.sol";
import "./util/Ownable.sol";
import "./SafeMath.sol";


contract Staking is Ownable{
    using SafeMath for uint256;

    // Staking Info of each user.
    struct UserInfo {
        uint256 amount;                             //staked amount of user 
        uint256 lastStakeTime;                      //last staking time of user
        bool validator;                             //true if user is validator    
        uint256 voteCount;                          //voted count as slash from other validators
        mapping(address => bool) votedAddresses;    //voted addresses to other users
    }

    // staking token and reward pool
    IERC20 public stakingToken;
    address public rewardPool;

    uint256 public apr = 30;                            //apr of staking         
    uint256 public totalStaked;                         //total staked amount    
    uint256 public validatorStakingLimit = 2000;        //limit to become a validator
    uint256 public voteCountLimit = 3;                  //if voted as slash 3 times, that user will be slashed

    mapping (address => UserInfo) public userInfo;      //all user info

    event Deposit(address user, uint256 amount);        //deposit event    
    event Withdraw(address user, uint256 amount);       //withdraw event

    constructor(
        address _token,                                 //staking token address
        address _rewardPool                             //reward pool address
    ) public {
        stakingToken = IERC20(_token);
        rewardPool = _rewardPool;
    }

    // only owner can update apr
    function updateApr(uint256 _apr) public onlyOwner {
        require(_apr>0, "apr set error");
        apr = _apr;
    }

    //get staked amount of user
    function getStakedAmount(address _user) external view returns (uint256) {
        return userInfo[_user].amount;
    }

    //get pending reward amount of user
    function pendingReward(address _user) public view returns (uint256) {
        UserInfo storage user = userInfo[_user];
        uint256 duration = block.timestamp-user.lastStakeTime;
        return user.amount.mul(1e10).mul(apr).mul(duration).div(365 days).div(100);
    }

    //stake
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

    //withdraw
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

    //update rewardPool address
    function setrewardPool(address _rewardPool) public {
        require(msg.sender == rewardPool, "invalid address");
        require(_rewardPool != address(this), "invalid address");
        require(_rewardPool != address(0), "invalid address");
        rewardPool = _rewardPool;
    }

    //validators can vote to slash bad user. can vote only once for a user
    //if slashed, his staking amount goes to reward pool
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