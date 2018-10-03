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

    constructor(address eip20in) public {
        eip20 = eip20in;
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
    event IntermediateStorage(string uriin, string hashin);
    enum EscrowStatuses { Launched, Pending, Partial, Paid, Complete, Cancelled }
    EscrowStatuses private status;

    address private reporc;
    address private recorc;

    uint256 private repfee;
    uint256 private recfee;

    address private canceler;
    address private eip20;

    string private manifestUrl;
    string private manifestHash;

    string private intermediateManifestUrl;
    string private intermediateManifestHash;

    string private resultsManifestUrl;
    string private resultsManifestHash;

    uint private expiration;

    constructor(address eip20in, address cancelerin, uint expirationin) public {
        eip20 = eip20in;
        canceler = cancelerin;
        status = EscrowStatuses.Launched;
        expiration = expirationin.add(block.timestamp); // solhint-disable-line not-rely-on-time
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
    // and assigs a reputation oracle to payout the bounty of size of the
    // amount specified
    function setup(address reporcin, address recorcin, uint256 recfeein, uint256 repfeein, uint256 amount, string urlin, string hash) public {
        require(expiration > block.timestamp);  // solhint-disable-line not-rely-on-time
        require(msg.sender == canceler);
        require(recfeein.add(repfeein) >= 0 && recfeein.add(repfeein) <= 100);
        require(getBalance() >= amount);
        require(status == EscrowStatuses.Launched);

        reporc = reporcin;
        recorc = recorcin;
        repfee = repfeein;
        recfee = recfeein;

        manifestUrl = urlin;
        manifestHash = hash;
        status = EscrowStatuses.Pending;
        emit Pending(manifestUrl, manifestHash);
    }

    function abort()  public {
        require(msg.sender == canceler);
        require(status != EscrowStatuses.Partial);
        require(status != EscrowStatuses.Complete);
        require(status != EscrowStatuses.Paid);
        killContract();
    }

    function complete() public returns (bool success) {
        require(expiration > block.timestamp);  // solhint-disable-line not-rely-on-time
        require(msg.sender == reporc);
        if (status == EscrowStatuses.Complete) {
            return true;
        }

        if (status == EscrowStatuses.Paid) {
            status = EscrowStatuses.Complete;
            return true;
        }
        return false;
    }

    function storeResults(string uriin, string hashin) public {
        require(expiration > block.timestamp);  // solhint-disable-line not-rely-on-time
        require(msg.sender == recorc);
        require(status == EscrowStatuses.Pending || status == EscrowStatuses.Partial);
        intermediateManifestUrl = uriin;
        intermediateManifestHash = hashin;
        emit IntermediateStorage(uriin, hashin);
    }

    function payOut(uint256 amount, address destination, string uriin, string hashin) public returns (bool) {
        require(expiration > block.timestamp);  // solhint-disable-line not-rely-on-time
        require(msg.sender == reporc);
        balance = getBalance();
        require(balance > 0);
        require(balance >= amount);
        require(status != EscrowStatuses.Launched);
        require(status != EscrowStatuses.Paid);
        resultsManifestUrl = uriin;
        resultsManifestHash = hashin;

        bool success = partialPayout(amount, destination, reporc, recorc);
        uint256 balance = getBalance();
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
        //kills contract and returns funds to buyer
    }

    // Nthing about this function actually requires a payout
    function partialPayout(uint256 _amount, address _destination, address _reporc, address _recorc) internal returns (bool) {
        EIP20Interface token = EIP20Interface(eip20);
        uint256 repAmount = repfee.div(100).mul(_amount);
        uint256 recAmount = recfee.div(100).mul(_amount);
        uint256 amount = _amount.sub(repAmount).sub(recAmount);
        token.transfer(reporc, repAmount);
        token.transfer(recorc, recAmount);
        token.transfer(_destination, amount);
        return true;
    }

    event Pending(string manifest, string hash);
}
