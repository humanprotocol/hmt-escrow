import * as React from 'react';
import { useFormContext, Controller } from 'react-hook-form';
import { Box, Chip, TextFieldProps } from '@mui/material';
import { TooltipWhite } from '../Tooltip';

import { CssTextField } from './style';

type MultiFormInputProps = {
  name: string;
  label: string;
  tooltipTitle?: string;
  variant?: string;
  type?: string;
} & TextFieldProps;

const MultiFormInput: React.FC<MultiFormInputProps> = ({
  name,
  tooltipTitle = '',
  variant = 'filled',
  type,
  label,
  ...otherProps
}) => {
  const [values, setValues] = React.useState<string[] | []>([]);
  const [currValue, setCurrValue] = React.useState('');

  const handleKeyPress = (e: any) => {
    if (e.keyCode === 32) {
      const current = e.target.value;
      e.preventDefault();
      setValues((prev: any) => {
        if (current === '' || prev.includes(current)) {
          return prev;
        }
        return [...prev, current];
      });
      setCurrValue('');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrValue(e.target.value);
  };

  const handleDelete = ({ index }: { item?: any; index: number }) => {
    const arr = [...values];
    arr.splice(index, 1);
    setValues(arr);
  };

  const {
    control,
    formState: { errors },
  } = useFormContext();

  return (
    <Controller
      control={control}
      name={name}
      render={({ field: { ref, onChange, value, ...rest } }) => (
        <TooltipWhite title={tooltipTitle} placement="top-start">
          <Box sx={{ position: 'relative' }}>
            <Box
              sx={{
                position: 'absolute',
                zIndex: '1',
                top: '1px',
                left: '12px',
              }}
            >
              {values &&
                values.map((item, index: number) => (
                  <Chip
                    key={`${item}`}
                    size="small"
                    onDelete={() => {
                      handleDelete({ item, index });
                      onChange();
                    }}
                    label={item}
                  />
                ))}
            </Box>
            <CssTextField
              {...otherProps}
              {...rest}
              label={!values.length ? label : ''}
              error={!!errors[name]}
              helperText={errors[name] ? errors[name]?.message : ''}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                handleChange(e);
                onChange(values);
              }}
              onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                handleKeyPress(e);
              }}
              fullWidth
              inputRef={ref}
              type={type}
              value={currValue}
              InputProps={{ style: { fontSize: 14 } }}
              variant={variant}
              sx={{
                mb: '1.5rem',
                backgroundColor: '#fff',
              }}
            />
          </Box>
        </TooltipWhite>
      )}
    />
  );
};

export default MultiFormInput;
