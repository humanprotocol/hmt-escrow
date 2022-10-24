import * as React from 'react';
import Box from '@mui/material/Box';
import { Stack, Typography } from '@mui/material';

import smallLogoSvg from 'src/assets/small-logo.svg';
import GithubIcon from './Icons/GithubIcon';
import DiscordIcon from './Icons/DiscordIcon';
import TwitterIcon from './Icons/TwitterIcon';
import TelegramIcon from './Icons/TelegramIcon';
import LinkedinIcon from './Icons/LinkedinIcon';

const Footer: React.FC = (): React.ReactElement => {
  return (
    <Box
      sx={{
        px: 12,
        pt: '12px',
        pb: '32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <img src={smallLogoSvg} alt="logo" />
        <Typography
          color="text.secondary"
          variant="caption"
          ml={2.5}
          lineHeight={1}
        >
          Terms and conditions
        </Typography>
      </Box>
      <Typography color="text.secondary" variant="caption">
        © {new Date().getFullYear()} HPF. HUMAN Protocol® is a registered
        trademark
      </Typography>
      <Stack direction="row" spacing={4}>
        <GithubIcon />
        <DiscordIcon />
        <TwitterIcon />
        <TelegramIcon />
        <LinkedinIcon />
      </Stack>
    </Box>
  );
};

export default Footer;
