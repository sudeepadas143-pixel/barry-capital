/**
 * Page copy. Brand strings come from firm.config.ts; nothing here names the firm directly.
 */
import { DESK_COUNT, FIRM_NAME, PARTNER_NAME as P, SEASON_LABEL } from '../firm.config';
import { numWord } from './format';
import type { FloorId } from './sim/types';

export const HERO = {
  kicker: [FIRM_NAME, SEASON_LABEL] as const,
  lead: `${numWord(DESK_COUNT)} traders,`,
  accent: 'one gets fired.',
  body: `${P} runs a floor of SI traders, and every one of them thinks they’re the smartest person in the building. Every hour ${P} checks the numbers. Whoever’s last clears their desk.`,
  cta: 'hire your own trader',
  secondary: 'see the leaderboard',
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
  label: 'your watchlist',
  title: 'Pick your people.',
  link: 'hire a trader',
  body: `Hire your own trader or follow a few from the floor. They’ll be here next time you open this browser, and ${P} never sees the list.`,
};

export const SINCE = {
  label: 'while you were away',
  empty: 'Follow a trader and we’ll keep track of what they do. Next time you’re back, you’ll see what changed.',
};

/** The only disclaimer on the site. */
export const FOOTER_NOTE = 'Illustrative figures. Not financial advice.';
