import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { FIRM_NAME, SEASON_START, SITE_DESCRIPTION, TICK_SECONDS } from './firm.config';
import { Engine } from './src/sim/engine';

/**
 * Bakes the firm's state as of build time into the bundle, so a first visit
 * only replays the minutes since the last deploy. The simulation is
 * deterministic, so this is purely a speed-up: any browser computing from
 * scratch lands on exactly the same state.
 */
function checkpoint(): Plugin {
  const id = 'virtual:checkpoint';
  return {
    name: 'firm-checkpoint',
    resolveId: (s) => (s === id ? `\0${id}` : null),
    load(s) {
      if (s !== `\0${id}`) return null;
      const e = new Engine({ seasonStart: SEASON_START, tickSeconds: TICK_SECONDS });
      e.advanceToTime(Date.now());
      return `export default ${JSON.stringify(e.state)};`;
    },
  };
}

/** Tells the app which optional art files exist, so it never requests missing ones. */
function artManifest(): Plugin {
  const id = 'virtual:art';
  const has = (p: string) => existsSync(resolve(__dirname, 'public/art', p));
  return {
    name: 'firm-art',
    resolveId: (s) => (s === id ? `\0${id}` : null),
    load(s) {
      if (s !== `\0${id}`) return null;
      return `export default ${JSON.stringify({
        building: has('building.png'),
        hotspots: has('hotspots.json'),
        foreground: has('foreground.png'),
        sprites: has('sprites/sprites.json'),
      })};`;
    },
  };
}

export default defineConfig({
  plugins: [
    react(),
    checkpoint(),
    artManifest(),
    {
      name: 'firm-html',
      transformIndexHtml: (html) =>
        html.replaceAll('%FIRM_NAME%', FIRM_NAME).replaceAll('%SITE_DESCRIPTION%', SITE_DESCRIPTION),
    },
  ],
});
