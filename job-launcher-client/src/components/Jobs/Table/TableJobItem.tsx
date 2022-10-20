/* eslint-disable camelcase */
import * as React from 'react';
import Box from '@mui/material/Box';
import Table from 'rc-table';
import { useTheme } from '@mui/material';
import { useParams } from 'react-router-dom';
import { styled } from '@mui/material/styles';
import { BoxContainer } from '../../Grid';
import { Backdrop } from '../../Backdrop';

import { useGetJobByIdQuery } from '../../../services/redux/api/jobApi';
import './style.css';
import { jobDetailsColumns } from './columns';
import { dateFormat, getTitle } from './helper';

export function TableJobItem() {
  const { id } = useParams();
  const { data, error, isLoading } = useGetJobByIdQuery(id);
  const [open, setOpen] = React.useState(false);
  const handleClose = (value: boolean) => {
    setOpen(value);
  };
  React.useEffect(() => {
    if (isLoading) {
      handleClose(true);
    } else {
      handleClose(false);
    }
  }, [isLoading]);

  const theme = useTheme();

  const values: any = [];

  if (!isLoading && data) {
    Object.entries(data).map(([prop, value]) => {
      if (prop === 'createdAt' || prop === 'updatedAt') {
        value = dateFormat(value);
      }
      if (prop === 'data') {
        return;
      }
      if (prop === 'url' || prop === 'updatedAt') {
        value = dateFormat(value);
      }
      if (prop === 'dataUrl') {
        const valueData: any = value;
        value = (
          <a target="_blank" href={String(value)} rel="noreferrer">
            {valueData}
          </a>
        );
      }
      if (prop === 'price') {
        const valueData: any = value;
        value = `${valueData} HMT`;
      }
      if (prop === 'userId') {
        return;
      }
      if (prop === 'labels') {
        const valueData: any = value;
        value = valueData.join(' ');
      }
      if (prop === 'requesterQuestionExample') {
        return;
      }
      if (value === '') {
        return;
      }
      return values.push({ prop: getTitle(prop), value });
    });
  }

  const BodyRow = styled('tr')({
    '& td': {
      transition: 'all 0.1s',
    },
    '&:hover td': {
      color: theme.palette.secondary.contrastText,
    },
  });

  const components = {
    body: {
      row: BodyRow,
    },
  };

  return (
    <>
      <BoxContainer>
        <Box sx={{ height: 400, width: '100%' }}>
          {!isLoading && values && (
            <Table
              columns={jobDetailsColumns}
              rowKey={(record: any) => record.id}
              data={values}
              components={components}
            />
          )}
          {error && <div>error</div>}
        </Box>
      </BoxContainer>
      <Backdrop open={open} handleClose={handleClose} />
    </>
  );
}
