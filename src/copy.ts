/**
 * Page copy. Brand strings come from firm.config.ts; nothing here names the firm directly.
 */
import { DESK_COUNT, FIRM_NAME, PARTNER_NAME as P, SEASON_LABEL } from '../firm.config';
import type { FloorId } from './sim/types';
import { numWord } from './format';

export const HERO = {
  kicker: [FIRM_NAME, SEASON_LABEL] as const,
  lead: 'serious suits.',
  accent: 'unserious coins.',
  body: `${FIRM_NAME} employs ${numWord(DESK_COUNT)} AI traders in good suits, each with a memecoin method of its own. ${P} reads the numbers every hour and decides who keeps a desk.`,
  cta: 'hire a trader',
  secondary: 'meet the traders',
};

export const FLOORS: { id: FloorId; name: string; blurb: string; floor: string }[] = [
  { id: 'office', name: 'the corner office', floor: 'sixth floor', blurb: `Where ${P} keeps the treasury, and a second copy of the treasury.` },
  { id: 'terminal', name: 'the terminal', floor: 'fifth floor', blurb: 'Every coin the firm is watching, on one board. Some of them leave. More arrive.' },
  { id: 'compliance', name: 'compliance', floor: 'fourth floor', blurb: 'Each trade is read back to the trader who made it. Nobody enjoys this.' },
  { id: 'hr', name: 'HR', floor: 'third floor', blurb: 'Headshots, employee files, and one cardboard box kept flat behind the door.' },
  { id: 'server', name: 'the server room', floor: 'basement', blurb: `When the board goes quiet, ${P} comes down here and waits for it to speak again.` },
  { id: 'lobby', name: 'the lobby', floor: 'ground floor', blurb: 'Coins come in through the revolving door. Most go out the same way.' },
];

export const PARTNER_AT: Record<FloorId | 'review', string[]> = {
  office: [`${P} is in the corner office, counting the treasury twice.`, `${P} is in the corner office, on hold with nobody.`],
  terminal: [`${P} is at the terminal, reading tickers aloud.`, `${P} is at the terminal, squinting at a four-letter ticker.`],
  compliance: [`${P} is in compliance, asking a trade to explain itself.`, `${P} is in compliance, initialling things.`],
  hr: [`${P} is in HR, updating the headshots.`, `${P} is in HR, folding a box.`],
  server: [`${P} is in the server room, waiting out a stale feed.`],
  lobby: [`${P} is in the lobby, hearing pitches.`, `${P} is in the lobby, turning down a coin named after a sandwich.`],
  review: [`${P} is on the fifth floor, doing performance reviews.`],
};

export const CORNER = {
  label: 'your corner of the firm',
  title: 'Take a seat.',
  link: 'hire a trader',
  body: `Hired traders and followed desks are kept in this browser. Nobody else sees them, including ${P}.`,
};

export const SINCE = {
  label: 'since the last visit',
  empty: 'Follow a trader and the minutes are kept here. Next time, you get only what changed.',
};

export const NOTE = `${SEASON_LABEL} · simulated balances, trades and prices. No funds deposited or withdrawn.`;
export const FOOTER_NOTE = 'Simulated. Not financial advice.';
