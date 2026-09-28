import type { Archetype, ArchetypeId } from './types';

export const ARCHETYPES: Record<ArchetypeId, Archetype> = {
  permabull: {
    id: 'permabull',
    title: 'the perma-bull',
    blurb: 'Has not had a bearish thought since orientation.',
    risk: 0.8,
    patience: 0.7,
  },
  trend: {
    id: 'trend',
    title: 'the trend follower',
    blurb: 'Buys whatever the rest of the floor is talking about.',
    risk: 0.6,
    patience: 0.3,
  },
  dip: {
    id: 'dip',
    title: 'the dip buyer',
    blurb: 'Considers every red candle a personal invitation.',
    risk: 0.6,
    patience: 0.5,
  },
  sniper: {
    id: 'sniper',
    title: 'the sniper',
    blurb: 'In within a minute of launch. Out before lunch.',
    risk: 0.9,
    patience: 0.15,
  },
  diamond: {
    id: 'diamond',
    title: 'the long-term holder',
    blurb: 'Has never sold anything. Describes this as a policy.',
    risk: 0.5,
    patience: 1,
  },
  fiver: {
    id: 'fiver',
    title: 'the five-percenter',
    blurb: 'Sells everything at plus five. Sleeps well.',
    risk: 0.3,
    patience: 0.2,
  },
  intern: {
    id: 'intern',
    title: 'the intern',
    blurb: 'Enthusiastic. Unsupervised. Small position sizes, for now.',
    risk: 0.5,
    patience: 0.4,
  },
  quant: {
    id: 'quant',
    title: 'the quant',
    blurb: 'Has a model. The model is two moving averages.',
    risk: 0.4,
    patience: 0.5,
  },
  stops: {
    id: 'stops',
    title: 'the risk manager',
    blurb: 'Tight stops on everything. Gets stopped out of everything.',
    risk: 0.2,
    patience: 0.3,
  },
  narrative: {
    id: 'narrative',
    title: 'the narrative trader',
    blurb: 'Buys the story. Reads the ticker, not the chart.',
    risk: 0.7,
    patience: 0.4,
  },
  averager: {
    id: 'averager',
    title: 'the averager',
    blurb: 'Buys more on the way down. Calls it conviction.',
    risk: 0.85,
    patience: 0.8,
  },
  contrarian: {
    id: 'contrarian',
    title: 'the contrarian',
    blurb: 'Only buys what nobody else on the floor holds.',
    risk: 0.55,
    patience: 0.6,
  },
};

export const ARCHETYPE_IDS = Object.keys(ARCHETYPES) as ArchetypeId[];
