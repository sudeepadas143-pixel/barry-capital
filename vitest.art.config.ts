import { defineConfig } from 'vitest/config';

/** Dev-only: renders the procedural scene to PNGs for review. `npm run art` */
export default defineConfig({
  test: { include: ['scripts/**/*.art.ts'], testTimeout: 60_000 },
});
