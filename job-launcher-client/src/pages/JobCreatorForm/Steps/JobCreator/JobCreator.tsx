import * as React from 'react';
import { SubmitHandler } from 'react-hook-form';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { IJobCreatorFormSchema } from './schema';

import { JobCreatorFormView } from './JobCreatorView';
import { useJobCreationFromDashMutation } from '../../../../services/redux/api/jobApi';
import { Backdrop } from '../../../../components/Backdrop';
import { transferERC20 } from '../../../../components/Eth/useEth';
import { makeTxHashSelector } from '../../../../services/redux/selectors/jobs';
import { setTx } from '../../../../services/redux/slices/jobSlice';

interface IJobCreatorFormStepOne {
  nextStep: () => void;
}
export const JobCreatorFormStepOne: React.FC<IJobCreatorFormStepOne> = ({
  nextStep,
}) => {
  const dispatch = useDispatch();
  const [valuesForm, setValues] = React.useState({});
  const [open, setOpen] = React.useState(false);

  const [createJob, { isLoading, isError, error, isSuccess }] =
    useJobCreationFromDashMutation();

  const handleClose = (value: boolean) => {
    setOpen(value);
  };

  const onSubmitHandler: SubmitHandler<IJobCreatorFormSchema> = (
    values: IJobCreatorFormSchema
  ) => {
    setValues(values);
    transferERC20({ fundAmount: values.price, backdropCallback: handleClose });
    handleClose(true);
  };

  const getTxHash = useSelector(makeTxHashSelector);
  React.useEffect(() => {
    if (getTxHash) {
      createJob({ ...valuesForm, transactionHash: getTxHash });
    }
    dispatch(setTx({ hash: null }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getTxHash]);

  React.useEffect(() => {
    if (isLoading) {
      handleClose(true);
    } else {
      handleClose(false);
    }
  }, [isLoading]);

  const navigate = useNavigate();
  React.useEffect(() => {
    if (isSuccess) {
      toast.success('Success');
      navigate('/job-created-success', { replace: true });
    }
    if (isError) {
      const errorData: any = error;
      toast.error(errorData.data.message, {
        position: 'top-right',
      });
    }
    if (error) {
      toast.error('oops something went wrong please try again', {
        position: 'top-right',
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [error, isError, isLoading, isSuccess]);
  return (
    <>
      <JobCreatorFormView
        onSubmitHandler={onSubmitHandler}
        nextStep={nextStep}
      />
      <Backdrop open={open} handleClose={handleClose} />
    </>
  );
};
