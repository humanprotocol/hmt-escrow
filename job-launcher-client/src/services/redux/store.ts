import { configureStore, combineReducers } from '@reduxjs/toolkit';
// import logger from 'redux-logger';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import { authApi } from './api/authApi';
import { userApi } from './api/userApi';
import userReducer from './slices/userSlice';
import authReducer from './slices/authSlice';
import jobsReducer from './slices/jobSlice';
import { jobApi } from './api/jobApi';

const rootReducer = combineReducers({
  [authApi.reducerPath]: authApi.reducer,
  [userApi.reducerPath]: userApi.reducer,
  [jobApi.reducerPath]: jobApi.reducer,
  auth: authReducer,
  user: userReducer,
  job: jobsReducer,
});

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({}).concat([
      // logger,
      jobApi.middleware,
      authApi.middleware,
      userApi.middleware,
    ]),
  devTools: process.env.NODE_ENV === 'development',
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
// router: connectRouter(history),
