import { FC } from 'react';
import { Main } from 'src/pages';

interface Route {
  key: string;
  title: string;
  path: string;
  enabled: boolean;
  component: FC<{}>;
}

export const routes: Array<Route> = [
  {
    key: 'main-route',
    title: 'Main',
    path: '/',
    enabled: true,
    component: Main,
  },
];
