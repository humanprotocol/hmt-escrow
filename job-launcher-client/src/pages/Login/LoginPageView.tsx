import * as React from 'react';
import {
  Grid,
  Box,
  Typography,
  Stack,
  // FormControlLabel,
  // Checkbox,
} from '@mui/material';
import LoadingButton from '@mui/lab/LoadingButton';
import { useForm, FormProvider } from 'react-hook-form';
import { literal, object, string, TypeOf } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import FormInput from '../../components/FormInput/FormInput';
import { BoxShadowContainer } from '../../components/Grid';
import { LinkItem } from './login.style';

const loginSchema = object({
  email: string().nonempty('Email is ').email('Email is invalid'),
  password: string()
    .nonempty('Password is ')
    .min(2, 'Password must be more than 2 characters')
    .max(32, 'Password must be less than 32 characters'),
  persistUser: literal(true).optional(),
});

export type ILoginSchema = TypeOf<typeof loginSchema>;

interface ILogin {
  onSubmitHandler: (values: ILoginSchema) => void;
}

export const LoginPageView: React.FC<ILogin> = ({ onSubmitHandler }) => {
  const defaultValues: ILoginSchema = {
    email: '',
    password: '',
  };

  const methods = useForm<ILoginSchema>({
    resolver: zodResolver(loginSchema),
    defaultValues,
  });

  return (
    <BoxShadowContainer>
      <FormProvider {...methods}>
        <Grid
          item
          container
          justifyContent="center"
          sx={{
            maxWidth: { sm: '40rem' },
            marginInline: 'auto',
          }}
        >
          <Grid item xs={12} sm={10}>
            <Box
              display="flex"
              flexDirection="column"
              component="form"
              noValidate
              autoComplete="on"
              sx={{ margin: '0 auto' }}
              onSubmit={methods.handleSubmit(onSubmitHandler)}
            >
              <FormInput
                label="Enter your email"
                type="email"
                name="email"
                autoComplete="login-email"
              />
              <FormInput
                type="password"
                label="Password"
                name="password"
                autoComplete="login-password"
              />
              <LoadingButton
                loading={false}
                type="submit"
                variant="contained"
                sx={{
                  py: '0.8rem',
                  mt: 2,
                  width: '80%',
                  marginInline: 'auto',
                }}
              >
                Login
              </LoadingButton>
            </Box>
          </Grid>
        </Grid>
        <Grid container justifyContent="center">
          <Stack sx={{ mt: '3rem', textAlign: 'center' }}>
            <Typography sx={{ fontSize: '0.9rem' }}>
              <LinkItem to="/forgot-password">Forgot your password?</LinkItem>
            </Typography>
          </Stack>
        </Grid>
      </FormProvider>
    </BoxShadowContainer>
  );
};
