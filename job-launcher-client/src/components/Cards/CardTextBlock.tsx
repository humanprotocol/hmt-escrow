import * as React from 'react';
import { Divider, Typography } from '@mui/material';

interface ICardTextBlock {
  title?: string;
  value: number | string;
}

export const CardTextBlock: React.FC<ICardTextBlock> = ({
  title,
  value,
}): React.ReactElement => (
  <>
    <Divider textAlign="center">
      <Typography variant="body2" color="text.secondary">
        {title}
      </Typography>
    </Divider>
    <Typography variant="body2" textAlign="center">
      {value}
    </Typography>
  </>
);
