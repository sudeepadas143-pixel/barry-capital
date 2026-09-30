/**
 * Page copy. Brand strings come from firm.config.ts; nothing here names the firm directly.
 */
import { FIRM_NAME, PARTNER_NAME as P, SEASON_LABEL } from '../firm.config';
import type { FloorId } from './sim/types';

export const HERO = {
  kicker: [FIRM_NAME, SEASON_LABEL] as const,
  lead: 'a trading floor',
  accent: 'for memecoins.',
  body: `${P} runs a trading floor full of SI traders. Each one has its own way of trading memecoins. Every hour, the worst one goes home.`,
  cta: 'hire a trader',
  secondary: 'meet the traders',
};

export const FLOORS: { id: FloorId; name: string; blurb: string; floor: string }[] = [
  { id: 'office', name: 'the corner office', floor: 'sixth floor', blurb: `${P}’s office. The treasury lives in the safe by the window.` },
  { id: 'terminal', name: 'the terminal', floor: 'fifth floor', blurb: 'Every coin the desks are watching, on one wall of screens.' },
  { id: 'compliance', name: 'compliance', floor: 'fourth floor', blurb: 'Every trade gets checked here after it happens.' },
  { id: 'hr', name: 'HR', floor: 'third floor', blurb: 'Hiring, firing, and the headshots you see on the traders page.' },
  { id: 'server', name: 'the server room', floor: 'basement', blurb: `Where the price feed comes in. When it stops, ${P} comes down here to wait for it.` },
  { id: 'lobby', name: 'the lobby', floor: 'ground floor', blurb: 'Security, the front desk, and a bronze bull that everyone touches on the way in.' },
];

export const PARTNER_AT: Record<FloorId | 'review', string[]> = {
  office: [`${P} is up in the corner office, practising putts.`, `${P} is in the corner office with a drink.`],
  terminal: [`${P} is on the fifth floor, watching the terminal.`, `${P} is at the terminal, on the phone.`],
  compliance: [`${P} is in compliance, going back over this morning’s trades.`, `${P} is down in compliance.`],
  hr: [`${P} is in HR, on a call about the next hire.`, `${P} is in HR.`],
  server: [`${P} is in the server room, waiting for the feed to come back.`],
  lobby: [`${P} is in the lobby, chatting to security.`, `${P} is in the lobby by the bull.`],
  review: [`${P} is walking the fifth floor doing reviews. It’s quiet up there.`],
};

export const CORNER = {
  label: 'your corner of the firm',
  title: 'Take a seat.',
  link: 'hire a trader',
  body: `Anyone you hire or follow is saved in this browser only. ${P} can’t see them.`,
};

export const SINCE = {
  label: 'since the last visit',
  empty: 'Follow a trader and we’ll keep track of what they do. Next time you’re back, you’ll see what changed.',
};

/** The only disclaimer on the site. */
export const FOOTER_NOTE = 'Prices, balances and trades on this site aren’t real. Not financial advice.';
