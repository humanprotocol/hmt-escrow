import jwtDecode from 'jwt-decode';
import { signIn, signOut } from '../../services/redux/slices/authSlice';
import { store } from '../../services/redux/store';

export function isJwtExpired(token: string) {
  const jwt: any = jwtDecode(token);
  const exp = jwt?.exp;
  console.log(exp, Date.now() >= exp * 1000);
  return Date.now() >= exp * 1000;
}

export async function init() {
  const token = localStorage.getItem('accessToken');
  //   const refreshToken = localStorage.getItem('refreshToken');
  if (token) {
    try {
      if (!isJwtExpired(token)) {
        store.dispatch(signIn());
      }
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
      store.dispatch(signOut());
    }
  } else {
    store.dispatch(signOut());
  }
}
