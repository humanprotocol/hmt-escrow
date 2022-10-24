import * as React from 'react';
import Box from '@mui/material/Box';
import { IconButton, Stack, Typography } from '@mui/material';

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
      <Stack direction="row" spacing={1}>
        <IconButton href="https://github.com/humanprotocol">
          <GithubIcon />
        </IconButton>
        <IconButton href="#">
          <DiscordIcon />
        </IconButton>
        <IconButton href="#">
          <TwitterIcon />
        </IconButton>
        <IconButton href="#">
          <TelegramIcon />
        </IconButton>
        <IconButton href="#">
          <LinkedinIcon />
        </IconButton>
      </Stack>
    </Box>
  );
};

export default Footer;
