import { Box } from '@mui/material';
import * as React from 'react';
import { WalletConnector } from '../WalletConnector';
import { Escrow } from './Escrow';
import { NetworkSwitcher } from './NetworkSwitcher';
import { useOnNetworkChange } from './useOnNetworkChange';
// import { switchNetwork } from '../WalletConnector/helpers';
// import { netCompare } from './helpers';

export const EscrowDashboard: React.FC = (): React.ReactElement => {
  const { onNetworkChange, setScannerUrl, escrowFactory, network } =
    useOnNetworkChange();

  // const handleSwitchNetwork = async (networkName: string) => {
  //   await switchNetwork({ networkName });
  // };

  // React.useEffect(() => {
  //   if (!window.ethereum) {
  //     toast.error(
  //       'Connect your Metamask wallet to update the message on the blockchain',
  //       {
  //         position: 'top-right',
  //       }
  //     );
  //     return;
  //   }

  //   if (netCompare({ network })) {
  //     handleSwitchNetwork(network);
  //   }
  // }, [network]);

  return (
    <>
      <Box
        sx={{
          display: 'flex',
          width: '400px',
          height: 'auto',
          alignContent: 'center',
          alignItems: 'center',
          mb: '20px ',
        }}
      >
        <Box sx={{ mr: '10px' }}>
          <WalletConnector />
        </Box>
        <NetworkSwitcher onNetworkChange={onNetworkChange} network={network} />
      </Box>
      <Escrow escrowFactory={escrowFactory} setScannerUrl={setScannerUrl} />
    </>
  );
};
