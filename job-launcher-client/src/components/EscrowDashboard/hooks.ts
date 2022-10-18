import * as React from 'react';
import { toast } from 'react-toastify';

import { ethers } from 'ethers';
import { networkMap } from '../../constants';
import { AppNetworkContext } from '../App/AppNetworkContext';
import { formatHexToNumber } from './helpers';

const EscrowFactoryABI = require('../../contracts/EscrowFactoryABI.json');

export const useEscrowHook = (
  escrowFactory: string,
  setScannerUrl: (url: string) => void
) => {
  const [latestEscrow, setLatestEscrow] = React.useState<string>(' ');
  const [counter, setCounter] = React.useState<string>('0');
  const { network } = React.useContext(AppNetworkContext);

  const { scanner, scannerUrl } = networkMap[network];

  React.useEffect(() => {
    if (scannerUrl) {
      setScannerUrl(scannerUrl);
    }
  }, [scannerUrl, setScannerUrl]);

  const address = networkMap[network].defaultFactoryAddr || escrowFactory;
  const { rpcUrl } = networkMap[network];

  const eventsUrl = `${scanner}/address/${address}#events`;

  React.useEffect(() => {
    async function setupEscrow() {
      try {
        const iface = new ethers.utils.Interface(EscrowFactoryABI);
        const httpProvider = new ethers.providers.JsonRpcProvider(rpcUrl);
        const Contract = new ethers.Contract(address, iface, httpProvider);

        const lastEscrow = await Contract.lastEscrow();
        setLatestEscrow(lastEscrow);

        const { _hex } = await Contract.counter();
        const count = formatHexToNumber({ hex: _hex, radix: 16 });
        setCounter(String(count));
      } catch (err) {
        const error: any = err;
        toast.error(error?.message, {
          position: 'top-right',
        });
        console.log(error);
      }
    }
    setupEscrow();
  }, [address, rpcUrl]);

  return { eventsUrl, latestEscrow, counter, address, scanner, scannerUrl };
};
