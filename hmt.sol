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


contract HMTokenInterface {
    /* This is a slight change to the ERC20 base standard.
    function totalSupply() constant returns (uint256 supply);
    is replaced with:
    uint256 public totalSupply;
    This automatically creates a getter function for the totalSupply.
    This is moved to the base contract since public getter functions are not
    currently recognised as an implementation of the matching abstract
    function by the compiler.
    */
    /// total amount of tokens
    uint256 public totalSupply;

    event Transfer(address indexed _from, address indexed _to, uint256 _value);
    event Approval(address indexed _owner, address indexed _spender, uint256 _value);

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

    function transferBulk(address[] memory _tos, uint256[] memory _values, uint256 _txId) public returns (uint256 _bulkCount);

    /// @notice `msg.sender` approves `_spender` to spend `_value` tokens
    /// @param _spender The address of the account able to transfer the tokens
    /// @param _value The amount of tokens to be approved for transfer
    /// @return Whether the approval was successful or not
    function approve(address _spender, uint256 _value) public returns (bool success);

    /// @param _owner The address of the account owning tokens
    /// @param _spender The address of the account able to transfer the tokens
    /// @return Amount of remaining tokens allowed to spent
    function allowance(address _owner, address _spender) public view returns (uint256 remaining);
}

contract HMToken is HMTokenInterface {
    using SafeMath for uint256;
    uint256 private constant MAX_UINT256 = 2**256 - 1;
    uint256 private constant BULK_MAX_VALUE = 1000000000 * (10 ** 18);
    uint32  private constant BULK_MAX_COUNT = 100;

    event BulkTransfer(uint256 indexed _txId, uint256 _bulkCount);
    event BulkApproval(uint256 indexed _txId, uint256 _bulkCount);

    mapping (address => uint256) private balances;
    mapping (address => mapping (address => uint256)) private allowed;

    string public name;
    uint8 public decimals;
    string public symbol;

    constructor(uint256 _totalSupply, string _name, uint8 _decimals, string _symbol) public {
        totalSupply = _totalSupply * (10 ** uint256(_decimals));
        name = _name;
        decimals = _decimals;
        symbol = _symbol;
        balances[msg.sender] = totalSupply;
    }

    function transfer(address _to, uint256 _value) public returns (bool success) {
        success = transferQuiet(_to, _value);
        require(success, "Transfer didn't succeed");
        return success;
    }

    function transferFrom(address _spender, address _to, uint256 _value) public returns (bool success) {
        uint256 _allowance = allowed[_spender][msg.sender];
        require(balances[_spender] >= _value && _allowance >= _value, "Spender balance or allowance too low");
        require(_to != address(0), "Can't send tokens to uninitialized address");

        balances[_spender] = balances[_spender].sub(_value);
        balances[_to] = balances[_to].add(_value);

        if (_allowance < MAX_UINT256) { // Special case to approve unlimited transfers
            allowed[_spender][msg.sender] = allowed[_spender][msg.sender].sub(_value);
        }

        emit Transfer(_spender, _to, _value);
        return true;
    }

    function balanceOf(address _owner) public view returns (uint256 balance) {
        return balances[_owner];
    }

    function approve(address _spender, uint256 _value) public returns (bool success) {
        require(_spender != address(0), "Token spender is an uninitialized address");
        
        allowed[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value); //solhint-disable-line indent, no-unused-vars
        return true;
    }

    function increaseApproval(address _spender, uint _delta) public returns (bool success) {
        require(_spender != address(0), "Token spender is an uninitialized address");
        
        uint _oldValue = allowed[msg.sender][_spender];
        if (_oldValue.add(_delta) < _oldValue || _oldValue.add(_delta) >= MAX_UINT256) { // Truncate upon overflow.
            allowed[msg.sender][_spender] = MAX_UINT256.sub(1);
        } else {
            allowed[msg.sender][_spender] = allowed[msg.sender][_spender].add(_delta);
        }
        emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
        return true;
    }

    function decreaseApproval(address _spender, uint _delta) public returns (bool success) {
        require(_spender != address(0), "Token spender is an uninitialized address");
        
        uint _oldValue = allowed[msg.sender][_spender];
        if (_delta > _oldValue) { // Truncate upon overflow.
            allowed[msg.sender][_spender] = 0;
        } else {
            allowed[msg.sender][_spender] = allowed[msg.sender][_spender].sub(_delta);
        }
        emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
        return true;
    }

    function allowance(address _owner, address _spender) public view returns (uint256 remaining) {
        return allowed[_owner][_spender];
    }

    function transferBulk(address[] _tos, uint256[] _values, uint256 _txId) public returns (uint256 _bulkCount) {
        require(_tos.length == _values.length, "Amount of recipients and values don't match");
        require(_tos.length < BULK_MAX_COUNT, "Too many recipients");

        uint256 _bulkValue = 0;
        for (uint j = 0; j < _tos.length; ++j) {
            _bulkValue = _bulkValue.add(_values[j]);
        }
        require(_bulkValue < BULK_MAX_VALUE, "Bulk value too high");

        _bulkCount = 0;
        bool _success;
        for (uint i = 0; i < _tos.length; ++i) {
            _success = transferQuiet(_tos[i], _values[i]);
            if (_success) {
                _bulkCount = _bulkCount.add(1);
            }
        }
        emit BulkTransfer(_txId, _bulkCount);
        return _bulkCount;
    }

    function approveBulk(address[] _spenders, uint256[] _values, uint256 _txId) public returns (uint256 _bulkCount) {
        require(_spenders.length == _values.length, "Amount of spenders and values don't match");
        require(_spenders.length < BULK_MAX_COUNT, "Too many spenders");

        uint256 _bulkValue = 0;
        for (uint j = 0; j < _spenders.length; ++j) {
            _bulkValue = _bulkValue.add(_values[j]);
        }
        require(_bulkValue < BULK_MAX_VALUE, "Bulk value too high");

        _bulkCount = 0;
        bool _success;
        for (uint i = 0; i < _spenders.length; ++i) {
            _success = increaseApproval(_spenders[i], _values[i]);
            if (_success) {
                _bulkCount = _bulkCount.add(1);
            }
        }
        emit BulkApproval(_txId, _bulkCount);
        return _bulkCount;
    }

    // Like transfer, but fails quietly.
    function transferQuiet(address _to, uint256 _value) internal returns (bool success) {
        if (_to == address(0)) return false; // Preclude burning tokens to uninitialized address.
        if (_to == address(this)) return false; // Preclude sending tokens to the contract.
        if (balances[msg.sender] < _value) return false;

        balances[msg.sender] = balances[msg.sender].sub(_value);
        balances[_to] = balances[_to].add(_value);

        emit Transfer(msg.sender, _to, _value);
        return true;
    }
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

    uint256[] private finalAmounts;

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
        return HMTokenInterface(eip20).balanceOf(address(this));
    }

    function getAddressBalance(address _address) public view returns (uint256) {
        require(_address != address(0), "Token spender is an uninitialized address");
        return HMTokenInterface(eip20).balanceOf(address(_address));
    }

    function getReputationOracle() public view returns (address) {
        return reputationOracle;
    } 

    function getRecordingOracle() public view returns (address) {
        return recordingOracle;
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
    function setup(
        address _reputationOracle, 
        address _recordingOracle, 
        uint256 _reputationOracleStake, 
        uint256 _recordingOracleStake, 
        uint256 _amount, 
        string _url, 
        string _hash
    ) public 
    {
        require(expiration > block.timestamp, "Contract expired");  // solhint-disable-line not-rely-on-time
        require(msg.sender == canceler, "Address calling not the canceler");
        require(_reputationOracle != address(0), "Token spender is an uninitialized address");
        require(_recordingOracle != address(0), "Token spender is an uninitialized address");
        require(
            _reputationOracleStake.add(_recordingOracleStake) >= 0 && 
            _reputationOracleStake.add(_recordingOracleStake) <= 100, 
            "Stake out of bounds"
        );
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
        require(
            status == EscrowStatuses.Pending || 
            status == EscrowStatuses.Partial, 
            "Escrow not in Pending or Partial status state"
        );
        intermediateManifestUrl = _url;
        intermediateManifestHash = _hash;
        emit IntermediateStorage(_url, _hash);
    }

    function payOut(
        uint256 _amount, 
        address _recipient, 
        string _url, 
        string _hash
    ) public returns (bool) 
    {
        require(expiration > block.timestamp, "Contract expired");  // solhint-disable-line not-rely-on-time
        require(msg.sender == reputationOracle, "Address calling not the reputation oracle");
        uint256 balance = getBalance();
        require(balance > 0, "EIP20 contract out of funds");
        require(balance >= _amount, "Amount too high");
        require(status != EscrowStatuses.Launched, "Escrow in Launched status state");
        require(status != EscrowStatuses.Paid, "Escrow in Paid status state");
        resultsManifestUrl = _url;
        resultsManifestHash = _hash;

        bool success = partialPayout(_amount, _recipient);
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

    function bulkPayOut(
        address[] _recipients, 
        uint256[] _amounts,
        string _url, 
        string _hash,
        uint256 _txId
    ) public returns (bool) 
    {
        require(expiration > block.timestamp, "Contract expired");  // solhint-disable-line not-rely-on-time
        require(msg.sender == reputationOracle, "Address calling not the reputation oracle");
        uint256 balance = getBalance();
        require(balance > 0, "EIP20 contract out of funds");
        require(status != EscrowStatuses.Launched, "Escrow in Launched status state");
        require(status != EscrowStatuses.Paid, "Escrow in Paid status state");

        resultsManifestUrl = _url;
        resultsManifestHash = _hash;

        (uint256 reputationOracleFee, uint256 recordingOracleFee) = finalizePayouts(_amounts);
        HMTokenInterface token = HMTokenInterface(eip20);
        token.transferBulk(_recipients, finalAmounts, _txId);
        bool success = token.transfer(reputationOracle, reputationOracleFee);
        success = token.transfer(recordingOracle, recordingOracleFee);

        balance = getBalance();
        if (balance > 0) {
            success = token.transfer(canceler, balance);
        }
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

    function finalizePayouts(uint256[] _amounts) public returns (uint256, uint256) {
        uint256 reputationOracleFee = 0;
        uint256 recordingOracleFee = 0;
        for (uint256 j; j < _amounts.length; j++) {
            uint256 singleReputationOracleFee = reputationOracleStake.mul(_amounts[j]).div(100);
            uint256 singleRecordingOracleFee = recordingOracleStake.mul(_amounts[j]).div(100);
            uint256 amount = _amounts[j].sub(singleReputationOracleFee).sub(singleRecordingOracleFee);
            reputationOracleFee = reputationOracleFee.add(singleReputationOracleFee);
            recordingOracleFee = recordingOracleFee.add(singleRecordingOracleFee);
            finalAmounts.push(amount);
        }
        return (reputationOracleFee, recordingOracleFee);
    }

    function partialPayout(uint256 _amount, address _recipient) internal returns (bool) {
        HMTokenInterface token = HMTokenInterface(eip20);
        uint256 reputationOracleFee = reputationOracleStake.mul(_amount).div(100);
        uint256 recordingOracleFee = recordingOracleStake.mul(_amount).div(100);
        uint256 amount = _amount.sub(reputationOracleFee).sub(recordingOracleFee);
        token.transfer(reputationOracle, reputationOracleFee);
        token.transfer(recordingOracle, recordingOracleFee);
        token.transfer(_recipient, amount);
        return true;
    }

    event Pending(string manifest, string hash);
}
