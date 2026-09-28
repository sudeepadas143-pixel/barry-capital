/// <reference types="vite/client" />

declare module 'virtual:checkpoint' {
  import type { SimState } from './sim/firm';
  const state: SimState;
  export default state;
}
