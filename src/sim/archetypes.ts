import type { Archetype, ArchetypeId } from './types';

export const ARCHETYPES: Record<ArchetypeId, Archetype> = {
  permabull: {
    id: 'permabull',
    title: 'the perma-bull',
    blurb: 'Only ever buys. Treats every red day as a sale.',
    risk: 0.8,
    patience: 0.7,
  },
  trend: {
    id: 'trend',
    title: 'the trend follower',
    blurb: 'Buys whatever is up the most this hour and gets out when it turns.',
    risk: 0.6,
    patience: 0.3,
  },
  dip: {
    id: 'dip',
    title: 'the dip buyer',
    blurb: 'Waits for a coin to drop hard, then buys it for the bounce.',
    risk: 0.6,
    patience: 0.5,
  },
  sniper: {
    id: 'sniper',
    title: 'the sniper',
    blurb: 'Buys coins within a couple of minutes of them going up on the board. Rarely holds for long.',
    risk: 0.9,
    patience: 0.15,
  },
  diamond: {
    id: 'diamond',
    title: 'the long-term holder',
    blurb: 'Buys new coins and holds them until they drop off the board.',
    risk: 0.5,
    patience: 1,
  },
  fiver: {
    id: 'fiver',
    title: 'the five-percenter',
    blurb: 'Takes five percent and moves on. Has done it hundreds of times.',
    risk: 0.3,
    patience: 0.2,
  },
  intern: {
    id: 'intern',
    title: 'the intern',
    blurb: 'Twenty-two, first job, no real method yet. Mostly buys whatever is trending on their phone.',
    risk: 0.5,
    patience: 0.4,
  },
  quant: {
    id: 'quant',
    title: 'the quant',
    blurb: 'Trades a moving-average crossover and will explain it if you ask.',
    risk: 0.4,
    patience: 0.5,
  },
  stops: {
    id: 'stops',
    title: 'the risk manager',
    blurb: 'Puts a tight stop-loss on everything and gets stopped out a lot.',
    risk: 0.2,
    patience: 0.3,
  },
  narrative: {
    id: 'narrative',
    title: 'the narrative trader',
    blurb: 'Buys whatever fits the day’s theme and doesn’t look at charts much.',
    risk: 0.7,
    patience: 0.4,
  },
  averager: {
    id: 'averager',
    title: 'the averager',
    blurb: 'Buys more every time a position falls and waits for it to come back.',
    risk: 0.85,
    patience: 0.8,
  },
  contrarian: {
    id: 'contrarian',
    title: 'the contrarian',
    blurb: 'Only buys coins nobody else on the floor is holding.',
    risk: 0.55,
    patience: 0.6,
  },
};

export const ARCHETYPE_IDS = Object.keys(ARCHETYPES) as ArchetypeId[];
