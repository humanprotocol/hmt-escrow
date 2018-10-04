pragma solidity 0.4.24;


/**
 * @title SafeMath
 * @dev Math operations with safety checks that revert on error
 */
library SafeMath {

    /**
    * @dev Multiplies two numbers, reverts on overflow.
    */
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
        // benefit is lost if 'b' is also tested.
        // See: https://github.com/OpenZeppelin/openzeppelin-solidity/pull/522
        if (a == 0) {
            return 0;
        }

        uint256 c = a * b;
        require(c / a == b);

        return c;
    }

    /**
    * @dev Integer division of two numbers truncating the quotient, reverts on division by zero.
    */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b > 0); // Solidity only automatically asserts when dividing by 0
        uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold

        return c;
    }

    /**
    * @dev Subtracts two numbers, reverts on overflow (i.e. if subtrahend is greater than minuend).
    */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a);
        uint256 c = a - b;

        return c;
    }

    /**
    * @dev Adds two numbers, reverts on overflow.
    */
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a);

        return c;
    }

    /**
    * @dev Divides two numbers and returns the remainder (unsigned integer modulo),
    * reverts when dividing by zero.
    */
    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b != 0);
        return a % b;
    }
}


contract EIP20Interface {
    /// total amount of tokens
    uint256 public totalSupply;

    function fund() public payable returns(bool success) { }  // solhint-disable-line no-empty-blocks

    /// @param _owner The address from which the balance will be retrieved
    /// @return The balance
    function balanceOf(address _owner) public view returns (uint256 balance);

    /// @notice send `_value` token to `_to` from `msg.sender`
    /// @param _to The address of the recipient
    /// @param _value The amount of token to be transferred
    /// @return Whether the transfer was successful or not
    function transfer(address _to, uint256 _value) public returns (bool success);

    /// @notice send `_value` token to `_to` from `_from` on the condition it is approved by `_from`
    /// @param _from The address of the sender
    /// @param _to The address of the recipient
    /// @param _value The amount of token to be transferred
    /// @return Whether the transfer was successful or not
    function transferFrom(address _from, address _to, uint256 _value) public returns (bool success);

    /// @notice `msg.sender` approves `_spender` to spend `_value` tokens
    /// @param _spender The address of the account able to transfer the tokens
    /// @param _value The amount of tokens to be approved for transfer
    /// @return Whether the approval was successful or not
    function approve(address _spender, uint256 _value) public returns (bool success);

    /// @param _owner The address of the account owning tokens
    /// @param _spender The address of the account able to transfer the tokens
    /// @return Amount of remaining tokens allowed to spent
    function allowance(address _owner, address _spender) public view returns (uint256 remaining);

    /* solhint-disable no-simple-event-func-name */
    event Transfer(address indexed _from, address indexed _to, uint256 _value);
    /* solhint-enable no-simple-event-func-name */

    event Approval(address indexed _owner, address indexed _spender, uint256 _value);
}


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


// An agentless escrow contract
contract Escrow {
    using SafeMath for uint256;
    event IntermediateStorage(string _url, string _hash);
    enum EscrowStatuses { Launched, Pending, Partial, Paid, Complete, Cancelled }
    EscrowStatuses private status;

    address private reputationOracle;
    address private recordingOracle;

    uint256 private reputationOracleStake;
    uint256 private recordingOracleStake;

    address private canceler;
    address private eip20;

    string private manifestUrl;
    string private manifestHash;

    string private intermediateManifestUrl;
    string private intermediateManifestHash;

    string private resultsManifestUrl;
    string private resultsManifestHash;

    uint private expiration;

    constructor(address _eip20, address _canceler, uint _expiration) public {
        eip20 = _eip20;
        canceler = _canceler;
        status = EscrowStatuses.Launched;
        expiration = _expiration.add(block.timestamp); // solhint-disable-line not-rely-on-time
    }

    function getStatus() public view returns (EscrowStatuses) {
        return status;
    }

    function getTokenAddress() public view returns (address) {
        return eip20;
    }

    function getBalance() public view returns (uint256) {
        return EIP20Interface(eip20).balanceOf(address(this));
    }

    function getHash() public view returns (string) {
        return manifestHash;
    }

    function getUrl() public view returns (string) {
        return manifestUrl;
    }

    function getIUrl() public view returns (string) {
        return intermediateManifestUrl;
    }

    function getIHash() public view returns (string) {
        return intermediateManifestHash;
    }

    function getFUrl() public view returns (string) {
        return resultsManifestUrl;
    }

    function getFHash() public view returns (string) {
        return resultsManifestHash;
    }

    // The escrower puts the Token in the contract without an agentless
    // and assigsn a reputation oracle to payout the bounty of size of the
    // amount specified
    function setup(address _reputationOracle, address _recordingOracle, uint256 _reputationOracleStake, uint256 _recordingOracleStake, uint256 _amount, string _url, string _hash) public {
        require(expiration > block.timestamp, "Contract expired");  // solhint-disable-line not-rely-on-time
        require(msg.sender == canceler, "Address calling not the canceler");
        require(_reputationOracleStake.add(_recordingOracleStake) >= 0 && reputationOracleStake.add(_recordingOracleStake) <= 100, "Stake out of bounds");
        require(getBalance() >= _amount, "Amount too high");
        require(status == EscrowStatuses.Launched, "Escrow not in Launched status state");

        reputationOracle = _reputationOracle;
        recordingOracle = _recordingOracle;
        reputationOracleStake = _reputationOracleStake;
        recordingOracleStake = _recordingOracleStake;
 
        manifestUrl = _url;
        manifestHash = _hash;
        status = EscrowStatuses.Pending;
        emit Pending(manifestUrl, manifestHash);
    }

    function abort()  public {
        require(msg.sender == canceler, "Address calling not the canceler");
        require(status != EscrowStatuses.Partial, "Escrow in Partial status state");
        require(status != EscrowStatuses.Complete, "Escrow in Complete status state");
        require(status != EscrowStatuses.Paid, "Escrow in Paid status state");
        killContract();
    }

    function complete() public returns (bool success) {
        require(expiration > block.timestamp, "Contract expired");  // solhint-disable-line not-rely-on-time
        require(msg.sender == reputationOracle, "Address calling not the reputation oracle");
        if (status == EscrowStatuses.Complete) {
            return true;
        }

        if (status == EscrowStatuses.Paid) {
            status = EscrowStatuses.Complete;
            return true;
        }
        return false;
    }

    function storeResults(string _url, string _hash) public {
        require(expiration > block.timestamp, "Contract expired");  // solhint-disable-line not-rely-on-time
        require(msg.sender == recordingOracle, "Address calling not the recording oracle");
        require(status == EscrowStatuses.Pending || status == EscrowStatuses.Partial, "Escrow not in Pending or Partial status state");
        intermediateManifestUrl = _url;
        intermediateManifestHash = _hash;
        emit IntermediateStorage(_url, _hash);
    }

    function payOut(uint256 _amount, address _recipient, string _url, string _hash) public returns (bool) {
        require(expiration > block.timestamp, "Contract expired");  // solhint-disable-line not-rely-on-time
        require(msg.sender == reputationOracle, "Address calling not the reputation oracle");
        uint256 balance = getBalance();
        require(balance > 0, "EIP20 contract out of funds");
        require(balance >= _amount, "Amount too high");
        require(status != EscrowStatuses.Launched, "Escrow in Launched status state");
        require(status != EscrowStatuses.Paid, "Escrow in Paid status state");
        resultsManifestUrl = _url;
        resultsManifestHash = _hash;

        bool success = partialPayout(_amount, _recipient, reputationOracle, recordingOracle);
        balance = getBalance();
        if (success) {
            if (status == EscrowStatuses.Pending) {
                status = EscrowStatuses.Partial;
            }
            if (balance == 0 && status != EscrowStatuses.Paid) {
                status = EscrowStatuses.Paid;
            }
        }
        return success;
    }

    function killContract() internal {
        status = EscrowStatuses.Cancelled;
        selfdestruct(canceler);
    }

    function partialPayout(uint256 _amount, address _recipient, address _reputationOracle, address _recordingOracle) internal returns (bool) {
        EIP20Interface token = EIP20Interface(eip20);
        uint256 reputationOracleFee = reputationOracleStake.div(100).mul(_amount);
        uint256 recordingOracleFee = recordingOracleStake.div(100).mul(_amount);
        uint256 amount = _amount.sub(reputationOracleFee).sub(recordingOracleFee);
        token.transfer(_reputationOracle, reputationOracleFee);
        token.transfer(_recordingOracle, recordingOracleFee);
        token.transfer(_recipient, amount);
        return true;
    }

    event Pending(string manifest, string hash);
}
