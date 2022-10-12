pragma solidity 0.6.6;

import "./UpgradableProxy.sol";

contract UChildERC20Proxy is UpgradableProxy {
    constructor(address _proxyTo)
        public
        UpgradableProxy(_proxyTo)
    {}
}
