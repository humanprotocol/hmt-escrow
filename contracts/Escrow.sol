pragma solidity 0.6.2;

import "./HMTokenInterface.sol";
import "./SafeMath.sol";


contract Escrow {
    using SafeMath for uint256;
    event IntermediateStorage(string _url, string _hash);
    enum EscrowStatuses {Launched, Pending, Partial, Paid, Complete, Cancelled}
    EscrowStatuses public status;

    address public reputationOracle;
    address public recordingOracle;
    address public launcher;
    address payable public canceler;

    uint256 public reputationOracleStake;
    uint256 public recordingOracleStake;

    address public eip20;

    string public manifestUrl;
    string public manifestHash;

    string public finalResultsUrl;
    string public finalResultsHash;

    uint256 public duration;

    uint256[] public finalAmounts;
    bool public bulkPaid;

    mapping(address => bool) public areTrustedHandlers;

    constructor(
        address _eip20,
        address payable _canceler,
        uint256 _duration,
        address[] memory _handlers
    ) public {
        eip20 = _eip20;
        status = EscrowStatuses.Launched;
        duration = _duration.add(block.timestamp); // solhint-disable-line not-rely-on-time
        launcher = msg.sender;
        canceler = _canceler;
        areTrustedHandlers[_canceler] = true;
        areTrustedHandlers[msg.sender] = true;
        addTrustedHandlers(_handlers);
    }

    function getBalance() public view returns (uint256) {
        return HMTokenInterface(eip20).balanceOf(address(this));
    }

    function getAddressBalance(address _address) public view returns (uint256) {
        require(
            _address != address(0),
            "Token spender is an uninitialized address"
        );
        return HMTokenInterface(eip20).balanceOf(address(_address));
    }

    function isTrustedHandler(address _handler) public view returns (bool) {
        return areTrustedHandlers[_handler];
    }

    function addTrustedHandlers(address[] memory _handlers) public {
        for (uint256 i = 0; i < _handlers.length; i++) {
            areTrustedHandlers[_handlers[i]] = true;
        }
    }

    // The escrower puts the Token in the contract without an agentless
    // and assigsn a reputation oracle to payout the bounty of size of the
    // amount specified
    function setup(
        address _reputationOracle,
        address _recordingOracle,
        uint256 _reputationOracleStake,
        uint256 _recordingOracleStake,
        string memory _url,
        string memory _hash
    ) public
    {
        require(duration > block.timestamp, "Contract expired"); // solhint-disable-line not-rely-on-time
        require(isTrustedHandler(msg.sender), "Address calling not trusted");
        require(
            _reputationOracle != address(0),
            "Invalid or missing token spender"
        );
        require(
            _recordingOracle != address(0),
            "Invalid or missing token spender"
        );
        uint256 totalStake = _reputationOracleStake.add(_recordingOracleStake);
        require(
            totalStake >= 0 && totalStake <= 100,
            "Stake out of bounds"
        );
        require(
            status == EscrowStatuses.Launched,
            "Escrow not in Launched status state"
        );

        reputationOracle = _reputationOracle;
        recordingOracle = _recordingOracle;
        areTrustedHandlers[reputationOracle] = true;
        areTrustedHandlers[recordingOracle] = true;

        reputationOracleStake = _reputationOracleStake;
        recordingOracleStake = _recordingOracleStake;

        manifestUrl = _url;
        manifestHash = _hash;
        status = EscrowStatuses.Pending;
        emit Pending(manifestUrl, manifestHash);
    }

    function abort() public {
        require(isTrustedHandler(msg.sender), "Address calling not trusted");
        require(
            status != EscrowStatuses.Complete,
            "Escrow in Complete status state"
        );
        require(status != EscrowStatuses.Paid, "Escrow in Paid status state");
        selfdestruct(canceler);
    }

    function cancel() public returns (bool) {
        require(isTrustedHandler(msg.sender), "Address calling not trusted");
        require(
            status != EscrowStatuses.Complete,
            "Escrow in Complete status state"
        );
        require(status != EscrowStatuses.Paid, "Escrow in Paid status state");
        uint256 balance = getBalance();
        require(balance != 0, "EIP20 contract out of funds");

        HMTokenInterface token = HMTokenInterface(eip20);
        bool success = token.transfer(canceler, balance);
        status = EscrowStatuses.Cancelled;

        return success;
    }

    function complete() public {
        require(duration > block.timestamp, "Contract expired"); // solhint-disable-line not-rely-on-time
        require(
            msg.sender == reputationOracle || areTrustedHandlers[msg.sender],
            "Address calling is not trusted"
        );

        require (status == EscrowStatuses.Paid, "Escrow not in Paid state");
        status = EscrowStatuses.Complete;
    }

    function storeResults(string memory _url, string memory _hash) public {
        require(duration > block.timestamp, "Contract expired"); // solhint-disable-line not-rely-on-time
        require(isTrustedHandler(msg.sender), "Address calling not trusted");
        require(
            status == EscrowStatuses.Pending ||
                status == EscrowStatuses.Partial,
            "Escrow not in Pending or Partial status state"
        );
        emit IntermediateStorage(_url, _hash);
    }

    function bulkPayOut(
        address[] memory _recipients,
        uint256[] memory _amounts,
        string memory _url,
        string memory _hash,
        uint256 _txId
    ) public returns (bool)
    {
        require(duration > block.timestamp, "Contract expired"); // solhint-disable-line not-rely-on-time
        require(isTrustedHandler(msg.sender), "Address calling not trusted");
        uint256 balance = getBalance();
        require(balance != 0, "EIP20 contract out of funds");
        require(
            status != EscrowStatuses.Launched,
            "Escrow in Launched status state"
        );
        require(status != EscrowStatuses.Paid, "Escrow in Paid status state");

        bulkPaid = false;
        uint256 aggregatedBulkAmount = 0;
        for (uint256 i; i < _amounts.length; i++) {
            aggregatedBulkAmount += _amounts[i];
        }

        if (balance < aggregatedBulkAmount) {
            return bulkPaid;
        }

        bool writeOnchain = bytes(_hash).length != 0 || bytes(_url).length != 0;
        if (writeOnchain) {
            // Be sure they are both zero if one of them is
            finalResultsUrl = _url;
            finalResultsHash = _hash;
        }

        (uint256 reputationOracleFee, uint256 recordingOracleFee) = finalizePayouts(_amounts);
        HMTokenInterface token = HMTokenInterface(eip20);
        if (
            token.transferBulk(_recipients, finalAmounts, _txId) ==
            _recipients.length
        ) {
            delete finalAmounts;
            bulkPaid = token.transfer(reputationOracle, reputationOracleFee) && token.transfer(recordingOracle, recordingOracleFee);
        }

        balance = getBalance();
        if (bulkPaid) {
            if (status == EscrowStatuses.Pending) {
                status = EscrowStatuses.Partial;
            }
            if (balance == 0 && status == EscrowStatuses.Partial) {
                status = EscrowStatuses.Paid;
            }
        }
        return bulkPaid;
    }

    function finalizePayouts(uint256[] memory _amounts) public returns (uint256, uint256) {
        uint256 reputationOracleFee = 0;
        uint256 recordingOracleFee = 0;
        for (uint256 j; j < _amounts.length; j++) {
            uint256 singleReputationOracleFee = reputationOracleStake
                .mul(_amounts[j])
                .div(100);
            uint256 singleRecordingOracleFee = recordingOracleStake
                .mul(_amounts[j])
                .div(100);
            uint256 amount = _amounts[j].sub(singleReputationOracleFee).sub(
                singleRecordingOracleFee
            );
            reputationOracleFee = reputationOracleFee.add(
                singleReputationOracleFee
            );
            recordingOracleFee = recordingOracleFee.add(
                singleRecordingOracleFee
            );
            finalAmounts.push(amount);
        }
        return (reputationOracleFee, recordingOracleFee);
    }

    event Pending(string manifest, string hash);
}
