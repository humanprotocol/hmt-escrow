import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { IJob, IJobDetails, ITx } from '../../types';

const initialState: IJob = {
  details: {
    price: 0,
    labels: [],
    dataUrl: '',
    networkId: 0,
    requestType: '',
    datasetLength: 0,
    annotationsPerImage: 0,
    requesterDescription: '',
    requesterAccuracyTarget: 0,
    // requesterQuestion: '',
    // requesterQuestionExample: '',
  },
  stepTwo: {
    mount: 0,
  },
  tx: {
    hash: null,
  },
};

export const jobSlice = createSlice({
  name: 'job',
  initialState,
  reducers: {
    setJobDetails: (state, action: PayloadAction<IJobDetails>) => {
      state.details = action.payload;
    },
    setPayment: (state, action: PayloadAction<IJob>) => {
      state.stepTwo = action.payload.stepTwo;
    },
    setTx: (state, action: PayloadAction<ITx>) => {
      state.tx.hash = action.payload.hash;
    },
  },
});

// Actions
export const { setJobDetails, setPayment, setTx } = jobSlice.actions;

// Reducer
const jobsReducer = jobSlice.reducer;
export default jobsReducer;
