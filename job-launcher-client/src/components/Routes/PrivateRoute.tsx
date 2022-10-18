import * as React from 'react';
import { useSelector } from 'react-redux';
import { Navigate, Outlet } from 'react-router-dom';
import {
  makeIsAuth,
  makeIsTokenAuthenticated,
  makeIsMetaMaskConnected,
} from '../../services/redux/selectors/auth';

export const PrivateAuthTokenRoute = () => {
  const getMakeIsAuth = useSelector(makeIsTokenAuthenticated);
  return getMakeIsAuth ? <Outlet /> : <Navigate to="/" />;
};

export const PrivateWeb3Route = () => {
  const getIsMetaMaskConnected = useSelector(makeIsMetaMaskConnected);
  return getIsMetaMaskConnected ? <Outlet /> : <Navigate to="/" />;
};

export const PrivateAuthRoute = () => {
  const getMakeIsAuth = useSelector(makeIsAuth);
  return getMakeIsAuth ? <Outlet /> : <Navigate to="/" />;
};
// import { SkeletonBase } from '../Skeletons';
// export interface IProps {
//   component: React.FC<{}>;
// }
// export const PrivateRoute = ({ component: Component }: IProps): any => {
//

//   if (!auth) return <Navigate to="/" replace />;
//   return (
//     <React.Suspense fallback={<SkeletonBase />}>
//       <Component />
//     </React.Suspense>
//   );
// };
