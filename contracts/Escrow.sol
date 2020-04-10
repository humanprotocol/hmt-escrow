pragma solidity 0.4.24;
import "./HMTokenInterface.sol";
import "./SafeMath.sol";


contract Escrow {
    using SafeMath for uint256;
    event IntermediateStorage(string _url, string _hash);
    enum EscrowStatuses {Launched, Pending, Partial, Paid, Complete, Cancelled}
    EscrowStatuses private status;

    address private reputationOracle;
    address private recordingOracle;
    address private launcher;
    address private canceler;

    uint256 private reputationOracleStake;
    uint256 private recordingOracleStake;

    address private eip20;

    string private manifestUrl;
    string private manifestHash;

    string private intermediateResultsUrl;
    string private intermediateResultsHash;

    string private finalResultsUrl;
    string private finalResultsHash;

    uint256 private expiration;

    uint256[] private finalAmounts;
    bool private bulkPaid;

    struct TrustedHandler {
        address handlerAddress;
        bool isTrusted;
    }

    mapping(address => TrustedHandler) public trustedHandlers;

    constructor(address _eip20, address _canceler, uint256 _expiration) public {
        eip20 = _eip20;
        status = EscrowStatuses.Launched;
        expiration = _expiration.add(block.timestamp); // solhint-disable-line not-rely-on-time
        launcher = msg.sender;
        canceler = _canceler;
        trustedHandlers[_canceler].isTrusted = true;
        trustedHandlers[msg.sender].isTrusted = true;
    }

    function getLauncher() public view returns (address) {
        return launcher;
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
        require(
            _address != address(0),
            "Token spender is an uninitialized address"
        );
        return HMTokenInterface(eip20).balanceOf(address(_address));
    }

    function getReputationOracle() public view returns (address) {
        return reputationOracle;
    }

    function getRecordingOracle() public view returns (address) {
        return recordingOracle;
    }

    function getManifestHash() public view returns (string) {
        return manifestHash;
    }

    function getManifestUrl() public view returns (string) {
        return manifestUrl;
    }

    function getIntermediateResultsUrl() public view returns (string) {
        return intermediateResultsUrl;
    }

    function getIntermediateResultsHash() public view returns (string) {
        return intermediateResultsHash;
    }

    function getFinalResultsUrl() public view returns (string) {
        return finalResultsUrl;
    }

    function getFinalResultsHash() public view returns (string) {
        return finalResultsHash;
    }

    function getBulkPaid() public view returns (bool) {
        return bulkPaid;
    }

    function isTrustedHandler(address _handler) public view returns (bool) {
        return trustedHandlers[_handler].isTrusted;
    }

    function addTrustedHandlers(address[] _handlers) public {
        for (uint256 i = 0; i < _handlers.length; i++) {
            trustedHandlers[_handlers[i]].isTrusted = true;
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
        string _url,
        string _hash
    ) public {
        require(expiration > block.timestamp, "Contract expired"); // solhint-disable-line not-rely-on-time
        require(isTrustedHandler(msg.sender), "Address calling not trusted");
        require(
            _reputationOracle != address(0),
            "Token spender is an uninitialized address"
        );
        require(
            _recordingOracle != address(0),
            "Token spender is an uninitialized address"
        );
        require(
            _reputationOracleStake.add(_recordingOracleStake) >= 0 &&
                _reputationOracleStake.add(_recordingOracleStake) <= 100,
            "Stake out of bounds"
        );
        require(
            status == EscrowStatuses.Launched,
            "Escrow not in Launched status state"
        );

        reputationOracle = _reputationOracle;
        recordingOracle = _recordingOracle;
        trustedHandlers[reputationOracle].isTrusted = true;
        trustedHandlers[recordingOracle].isTrusted = true;

        reputationOracleStake = _reputationOracleStake;
        recordingOracleStake = _recordingOracleStake;
        bulkPaid = false;

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
        require(balance > 0, "EIP20 contract out of funds");

        HMTokenInterface token = HMTokenInterface(eip20);
        bool success = token.transfer(canceler, balance);
        status = EscrowStatuses.Cancelled;

        return success;
    }

    function complete() public {
        require(expiration > block.timestamp, "Contract expired"); // solhint-disable-line not-rely-on-time
        require(
            msg.sender == reputationOracle,
            "Address calling not the reputation oracle"
        );

        if (status == EscrowStatuses.Paid) {
            status = EscrowStatuses.Complete;
        }
    }

    function storeResults(string _url, string _hash) public {
        require(expiration > block.timestamp, "Contract expired"); // solhint-disable-line not-rely-on-time
        require(isTrustedHandler(msg.sender), "Address calling not trusted");
        require(
            status == EscrowStatuses.Pending ||
                status == EscrowStatuses.Partial,
            "Escrow not in Pending or Partial status state"
        );
        intermediateResultsUrl = _url;
        intermediateResultsHash = _hash;
        emit IntermediateStorage(_url, _hash);
    }

    function bulkPayOut(
        address[] _recipients,
        uint256[] _amounts,
        string _url,
        string _hash,
        uint256 _txId
    ) public returns (bool) {
        require(expiration > block.timestamp, "Contract expired"); // solhint-disable-line not-rely-on-time
        require(isTrustedHandler(msg.sender), "Address calling not trusted");
        uint256 balance = getBalance();
        require(balance > 0, "EIP20 contract out of funds");
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

        finalResultsUrl = _url;
        finalResultsHash = _hash;

        (
            uint256 reputationOracleFee,
            uint256 recordingOracleFee
        ) = finalizePayouts(_amounts);
        HMTokenInterface token = HMTokenInterface(eip20);
        if (
            token.transferBulk(_recipients, finalAmounts, _txId) ==
            _recipients.length
        ) {
            delete finalAmounts;
            bulkPaid = token.transfer(reputationOracle, reputationOracleFee);
            bulkPaid = token.transfer(recordingOracle, recordingOracleFee);
        }

        balance = getBalance();
        if (bulkPaid) {
            if (status == EscrowStatuses.Pending) {
                status = EscrowStatuses.Partial;
            }
            if (
                balance == 0 &&
                (status == EscrowStatuses.Pending ||
                    status == EscrowStatuses.Partial)
            ) {
                status = EscrowStatuses.Paid;
            }
        }
        return bulkPaid;
    }

    function finalizePayouts(uint256[] _amounts)
        public
        returns (uint256, uint256)
    {
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
