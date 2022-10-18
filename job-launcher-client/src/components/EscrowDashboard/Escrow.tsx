import * as React from 'react';

import { EscrowFactoryView } from './EscrowFactoryView';
import { useEscrowHook } from './hooks';

interface IEscrowContainer {
  escrowFactory: string;
  setScannerUrl: (url: string) => void;
}

export const Escrow: React.FC<IEscrowContainer> = ({
  escrowFactory,
  setScannerUrl,
}): React.ReactElement => {
  const { eventsUrl, latestEscrow, counter, address, scanner } = useEscrowHook(
    escrowFactory,
    setScannerUrl
  );

  return (
    <EscrowFactoryView
      latestEscrow={latestEscrow}
      eventsUrl={eventsUrl}
      scanner={scanner}
      address={address}
      count={counter}
    />
  );
};
