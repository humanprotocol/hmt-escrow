import * as React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import { CardTextBlock } from '../Cards';
import Events from './Events';

interface IEscrow {
  count: string;
  address: string;
  latestEscrow: string;
  eventsUrl: string;
  scanner: string;
}

export const EscrowFactoryView: React.FC<IEscrow> = ({
  count,
  address,
  latestEscrow,
  eventsUrl,
  scanner,
}): React.ReactElement => {
  return (
    <Card variant="outlined">
      <CardContent>
        <CardTextBlock title="Address" value={address} />
        <CardTextBlock title="Latest Escrow" value={latestEscrow} />
        <CardTextBlock title="Amount of jobs" value={count} />
        <Events url={eventsUrl} scanner={scanner} />
      </CardContent>
    </Card>
  );
};
