pragma solidity 0.4.24;
import "./HMTokenInterface.sol";
import "./helpers/SafeMath.sol";

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
