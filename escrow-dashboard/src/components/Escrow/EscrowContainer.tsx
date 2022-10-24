import * as React from 'react';
import { Box } from '@mui/material';

import networkSvg from 'src/assets/network.svg';
import ViewTitle from 'src/components/ViewTitle';

import { EscrowView } from './EscrowView';
import { NetworkTab } from './NetworkTab';

interface IEscrowContainer {}

export const EscrowContainer: React.FC<IEscrowContainer> =
  (): React.ReactElement => {
    return (
      <Box>
        <ViewTitle title="Network" iconUrl={networkSvg} />
        <NetworkTab />
        <EscrowView />
      </Box>
    );
  };
