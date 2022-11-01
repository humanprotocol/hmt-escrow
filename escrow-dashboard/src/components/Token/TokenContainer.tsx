import * as React from 'react';
import { Box } from '@mui/material';

import tokenSvg from 'src/assets/token.svg';
import ViewTitle from 'src/components/ViewTitle';

import { TokenView } from './TokenView';

interface ITokenContainer {}

export const TokenContainer: React.FC<
  ITokenContainer
> = (): React.ReactElement => {
  return (
    <Box mt={{ xs: 4, md: 8 }}>
      <ViewTitle title="Token" iconUrl={tokenSvg} />
      <Box mt={{ xs: 4, md: 8 }}>
        <TokenView />
      </Box>
    </Box>
  );
};
