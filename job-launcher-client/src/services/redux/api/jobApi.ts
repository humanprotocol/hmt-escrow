import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { IJobDetails } from '../../types';
import { BASE_URL } from './constants';

export const jobApi = createApi({
  reducerPath: 'jobApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${BASE_URL}/`,
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
        headers.set('Access-Control-Allow-Origin', '*');
      }
      return headers;
    },
    credentials: 'include',
  }),
  endpoints: (builder) => ({
    jobCreation: builder.mutation<IJobDetails, any>({
      query(data) {
        return {
          url: 'job',
          method: 'POST',
          body: data,
        };
      },
      transformResponse: (result: { data: any }) => {
        // console.log(result, 'transformResponse');
        return result.data;
      },
      // eslint-disable-next-line no-unused-vars
      async onQueryStarted(args, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          console.log(data, 'job');
        } catch (error) {
          console.log(error);
        }
      },
    }),
    jobCreationFromDash: builder.mutation<IJobDetails, any>({
      query(data) {
        return {
          url: 'job',
          method: 'POST',
          body: data,
        };
      },
      transformResponse: (result: { data: any }) => {
        return result.data;
      },
      // eslint-disable-next-line no-unused-vars
      async onQueryStarted(args, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          console.log(data, 'job');
        } catch (error) {
          console.log(error);
        }
      },
    }),
    getJobs: builder.query({
      query: () => '/job',
    }),
    getJobById: builder.query({
      query: (id) => ({ url: `/job/${id}` }),
    }),
  }),
});

export const {
  useJobCreationMutation,
  useJobCreationFromDashMutation,
  useGetJobsQuery,
  useGetJobByIdQuery,
} = jobApi;
