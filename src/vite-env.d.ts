/// <reference types="vite/client" />

declare module 'virtual:checkpoint' {
  import type { SimState } from './sim/firm';
  const state: SimState;
  export default state;
}

declare module 'virtual:art' {
  const art: { building: boolean; hotspots: boolean; foreground: boolean; sprites: boolean };
  export default art;
}
