import { Grid, Box } from '@mui/material';
import LoadingButton from '@mui/lab/LoadingButton';
import * as React from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { object, string, TypeOf } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import FormInput from '../../components/FormInput/FormInput';
import { BoxShadowContainer } from '../../components/Grid/Grid';

const signUpSchema = object({
  email: string().nonempty('Email is ').email('Email is invalid'),
  password: string()
    .nonempty('Password is ')
    .min(3, 'Password must be more than 3 characters')
    .max(32, 'Password must be less than 32 characters'),
  confirm: string().nonempty('Please confirm your password'),
}).refine((data) => data.password === data.confirm, {
  path: ['confirm'],
  message: 'Passwords do not match',
});

export type ISignUpSchema = TypeOf<typeof signUpSchema>;

interface ISignUp {
  onSubmitHandler: (values: ISignUpSchema) => void;
}

export const SignUpView: React.FC<ISignUp> = ({ onSubmitHandler }) => {
  const defaultValues: ISignUpSchema = {
    email: '',
    password: '',
    confirm: '',
  };

  const methods = useForm<ISignUpSchema>({
    resolver: zodResolver(signUpSchema),
    defaultValues,
  });

  return (
    <BoxShadowContainer>
      <FormProvider {...methods}>
        <Grid
          item
          container
          justifyContent="center"
          rowSpacing={5}
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
                autoComplete="sign-up-email"
              />
              <FormInput
                type="password"
                label="Password"
                name="password"
                autoComplete="password"
              />
              <FormInput
                type="password"
                label="Confirm Password"
                name="confirm"
                autoComplete="confirm"
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
                Sign Up
              </LoadingButton>
            </Box>
          </Grid>
        </Grid>
      </FormProvider>
    </BoxShadowContainer>
  );
};
