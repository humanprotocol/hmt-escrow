import * as React from 'react';
import { Route, Routes, BrowserRouter } from 'react-router-dom';
import { Provider as ReduxProvider } from 'react-redux';
import { ApolloProvider } from '@apollo/client';
import { ToastContainer } from 'react-toastify';
import { ThemeProvider } from '@mui/material/styles';
import { Web3ReactProvider } from '@web3-react/core';
import { store } from '../../services/redux/store';
// import { routes as appRoutes } from '../Routes/routes';
// import { Layout } from '../Layouts';
import theme from '../../ui/theme';
import Home from '../../pages/Home';
import { PrivateAuthTokenRoute } from '../Routes';

import 'react-toastify/dist/ReactToastify.css';
// import { PrivateRoute } from '../Routes';

import { SignUp } from '../../pages/SignUp/SignUp';
import Login from '../../pages/Login';
import RestorePassword from '../../pages/RestorePassword';
import { JobCreatorForm } from '../../pages/JobCreatorForm/JobCreatorForm';
import { getClient, getLibrary } from './utils';
import { ConfirmStep } from '../../pages/JobCreatorForm/Steps/ConfirmStep';
import { TableDataGrid } from '../Jobs/Table';

import { DashboardLayout } from '../Layouts/DashboardLayout';
import { AppNetworkContext } from './AppNetworkContext';
import { networkMap } from '../../constants';
import { TableJobItem } from '../Jobs/Table/TableJobItem';

export const App = () => {
  const [network, setNetwork] = React.useState<string>('polygon');
  return (
    <React.StrictMode>
      <ReduxProvider store={store}>
        <Web3ReactProvider getLibrary={getLibrary}>
          <BrowserRouter>
            <AppNetworkContext.Provider value={{ network, setNetwork }}>
              <ApolloProvider
                client={getClient(networkMap[network].graphqlClientUrl)}
              >
                <DashboardLayout>
                  <ThemeProvider theme={theme}>
                    <Routes>
                      <Route path="/" element={<Home />} />
                      <Route element={<PrivateAuthTokenRoute />}>
                        <Route
                          path="/job-create"
                          element={<JobCreatorForm />}
                        />
                      </Route>
                      <Route element={<PrivateAuthTokenRoute />}>
                        <Route
                          path="/job-created-success"
                          element={<ConfirmStep />}
                        />
                      </Route>
                      <Route element={<PrivateAuthTokenRoute />}>
                        <Route path="/jobs" element={<TableDataGrid />} />
                      </Route>
                      <Route element={<PrivateAuthTokenRoute />}>
                        <Route path="/job/:id" element={<TableJobItem />} />
                      </Route>
                      <Route path="/login" element={<Login />} />
                      <Route path="/signup" element={<SignUp />} />
                      <Route
                        path="/forgot-password"
                        element={<RestorePassword />}
                      />
                    </Routes>
                  </ThemeProvider>
                </DashboardLayout>
                <ToastContainer />
              </ApolloProvider>
            </AppNetworkContext.Provider>
          </BrowserRouter>
        </Web3ReactProvider>
      </ReduxProvider>
    </React.StrictMode>
  );
};

// {
//   /* {appRoutes.map((route) => (
//                   <Route
//                     key={route.key}
//                     path={route.path}
//                     element={<PrivateRoute component={route.component} />}
//                   />
//                 ))} */
// }
