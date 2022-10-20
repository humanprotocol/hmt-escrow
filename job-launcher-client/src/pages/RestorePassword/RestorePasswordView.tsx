import * as React from 'react';
import { Grid, Box } from '@mui/material';
import LoadingButton from '@mui/lab/LoadingButton';
import { useForm, FormProvider } from 'react-hook-form';
import { object, string, TypeOf } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import FormInput from '../../components/FormInput/FormInput';
import { BoxShadowContainer } from '../../components/Grid';

const restoreSchema = object({
  email: string().nonempty('Email is required').email('Email is invalid'),
});

export type IRestoreSchema = TypeOf<typeof restoreSchema>;

interface ILogin {
  onSubmitHandler: (values: IRestoreSchema) => void;
}

export const RestorePasswordView: React.FC<ILogin> = ({ onSubmitHandler }) => {
  const defaultValues: IRestoreSchema = {
    email: '',
  };

  const methods = useForm<IRestoreSchema>({
    resolver: zodResolver(restoreSchema),
    defaultValues,
  });

  return (
    <BoxShadowContainer>
      <FormProvider {...methods}>
        <Grid container>
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
                autoComplete="off"
                sx={{ paddingRight: { sm: '3rem' } }}
                onSubmit={methods.handleSubmit(onSubmitHandler)}
              >
                <FormInput
                  label="Enter your email"
                  type="email"
                  name="email"
                  focused
                  required
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
                  Restore password
                </LoadingButton>
              </Box>
            </Grid>
          </Grid>
        </Grid>
      </FormProvider>
    </BoxShadowContainer>
  );
};
