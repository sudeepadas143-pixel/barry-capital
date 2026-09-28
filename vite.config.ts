import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { FIRM_NAME, SITE_DESCRIPTION } from './firm.config';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'firm-html',
      transformIndexHtml: (html) =>
        html
          .replaceAll('%FIRM_NAME%', FIRM_NAME)
          .replaceAll('%SITE_DESCRIPTION%', SITE_DESCRIPTION),
    },
  ],
});
