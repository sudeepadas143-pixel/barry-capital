import type { Archetype, ArchetypeId } from './types';

export const ARCHETYPES: Record<ArchetypeId, Archetype> = {
  permabull: {
    id: 'permabull',
    title: 'the perma-bull',
    blurb: 'Has never had a bearish thought. Says bears are poor, usually out loud.',
    risk: 0.8,
    patience: 0.7,
  },
  trend: {
    id: 'trend',
    title: 'the trend follower',
    blurb: 'Buys whatever the floor is shouting about, then says they called it.',
    risk: 0.6,
    patience: 0.3,
  },
  dip: {
    id: 'dip',
    title: 'the dip buyer',
    blurb: 'Sees a red candle and hears a dinner bell.',
    risk: 0.6,
    patience: 0.5,
  },
  sniper: {
    id: 'sniper',
    title: 'the sniper',
    blurb: 'In within a minute of launch. Tells everyone about the four seconds.',
    risk: 0.9,
    patience: 0.15,
  },
  diamond: {
    id: 'diamond',
    title: 'the long-term holder',
    blurb: 'Has never sold anything. Calls it diamond hands. Calls you paper hands.',
    risk: 0.5,
    patience: 1,
  },
  fiver: {
    id: 'fiver',
    title: 'the five-percenter',
    blurb: 'Sells everything at plus five and does a lap of the floor about it.',
    risk: 0.3,
    patience: 0.2,
  },
  intern: {
    id: 'intern',
    title: 'the intern',
    blurb: 'Twenty-two. Unsupervised. Already talks about their future yacht.',
    risk: 0.5,
    patience: 0.4,
  },
  quant: {
    id: 'quant',
    title: 'the quant',
    blurb: 'Has a model. The model is two moving averages. Will explain it anyway.',
    risk: 0.4,
    patience: 0.5,
  },
  stops: {
    id: 'stops',
    title: 'the risk manager',
    blurb: 'Tight stops, tight collar, tighter smile. Gets stopped out of everything.',
    risk: 0.2,
    patience: 0.3,
  },
  narrative: {
    id: 'narrative',
    title: 'the narrative trader',
    blurb: 'Doesn’t read charts. Reads the room, then sells it a story.',
    risk: 0.7,
    patience: 0.4,
  },
  averager: {
    id: 'averager',
    title: 'the averager',
    blurb: 'Buys more on the way down. Calls it conviction. Sweats a little.',
    risk: 0.85,
    patience: 0.8,
  },
  contrarian: {
    id: 'contrarian',
    title: 'the contrarian',
    blurb: 'Only buys what nobody else holds, so nobody else can be right.',
    risk: 0.55,
    patience: 0.6,
  },
};

export const ARCHETYPE_IDS = Object.keys(ARCHETYPES) as ArchetypeId[];
