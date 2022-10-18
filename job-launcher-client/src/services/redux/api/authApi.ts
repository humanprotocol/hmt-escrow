import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { toast } from 'react-toastify';
import { ILoginSchema } from '../../../pages/Login/LoginPageView';
import { IRestoreSchema } from '../../../pages/RestorePassword/RestorePasswordView';
import { ISignUpSchema } from '../../../pages/SignUp/SignUpView';
import { IToken, IGenericResponse } from './types';
import { authSlice } from '../slices/authSlice';
import { BASE_URL } from './constants';

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${BASE_URL}/auth/`,
    prepareHeaders: (headers) => {
      headers.set('Access-Control-Allow-Origin', 'no-cors');
      return headers;
    },
    credentials: 'include',
  }),
  endpoints: (builder) => ({
    signUpUser: builder.mutation<IToken, ISignUpSchema>({
      query(data) {
        return {
          url: 'signup',
          method: 'POST',
          body: data,
          credentials: 'include',
        };
      },
      async onQueryStarted(args, { dispatch, queryFulfilled }) {
        try {
          const {
            data: { accessToken, refreshToken },
          } = await queryFulfilled;

          if (accessToken && refreshToken) {
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('refreshToken', refreshToken);
            dispatch(authSlice.actions.setAuth({ isAuth: true }));
          }

          // await dispatch(userApi.endpoints.setUser.initiate(null));
        } catch (error) {
          console.log(error);
          toast.error('Please try again', {
            position: 'top-right',
          });
        }
      },
    }),
    loginUser: builder.mutation<IToken, ILoginSchema>({
      query(data) {
        return {
          url: 'signin',
          method: 'POST',
          body: data,
          credentials: 'include',
        };
      },
      async onQueryStarted(args, { dispatch, queryFulfilled }) {
        try {
          const {
            data: { accessToken, refreshToken },
          } = await queryFulfilled;

          if (accessToken && refreshToken) {
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('refreshToken', refreshToken);
            dispatch(authSlice.actions.setAuth({ isAuth: true }));
          }

          // await dispatch(userApi.endpoints.setUser.initiate(null));
        } catch (error) {
          console.log(error);
          toast.error('Please try again', {
            position: 'top-right',
          });
        }
      },
    }),
    // complete call
    logoutUser: builder.mutation<void, void>({
      query() {
        localStorage.clear();
        return {
          url: 'signOut',
          credentials: 'include',
        };
      },
    }),
    // complete call
    refreshToken: builder.mutation<IGenericResponse, any>({
      query(data) {
        // const checkTokenExpirationMiddleware = store => next => action => {
        //   const token =
        //     JSON.parse(localStorage.getItem("user")) &&
        //     JSON.parse(localStorage.getItem("user"))["token"];
        //   if (jwtDecode(token).exp < Date.now() / 1000) {
        //     next(action);
        //     localStorage.clear();
        //   }
        return {
          url: 'refresh',
          method: 'POST',
          body: data,
        };
      },
    }),
    forgotPassword: builder.mutation<IGenericResponse, IRestoreSchema>({
      query(data) {
        return {
          url: 'forgot-password',
          method: 'POST',
          body: data,
        };
      },
    }),
    restorePassword: builder.mutation<IGenericResponse, IRestoreSchema>({
      query(data) {
        return {
          url: 'forgot-password',
          method: 'POST',
          body: data,
        };
      },
    }),
    // complete call
    verifyEmail: builder.mutation<IGenericResponse, any>({
      query(data) {
        return {
          url: 'email-verification',
          method: 'POST',
          body: data,
        };
      },
    }),
    // complete call
    resendEmailVerification: builder.mutation<IGenericResponse, any>({
      query(data) {
        return {
          url: 'resend-email-verification',
          method: 'POST',
          body: data,
        };
      },
    }),
  }),
});

export const {
  useSignUpUserMutation,
  useLoginUserMutation,
  useLogoutUserMutation,
  useRefreshTokenMutation,
  useForgotPasswordMutation,
  useRestorePasswordMutation,
  useVerifyEmailMutation,
  useResendEmailVerificationMutation,
} = authApi;
