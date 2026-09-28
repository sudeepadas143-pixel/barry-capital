const MINUS = '−';

export function fmtPct(p: number, digits = 1): string {
  const r = Number(p.toFixed(digits));
  if (r === 0) return `${(0).toFixed(digits)}%`;
  return `${r > 0 ? '+' : MINUS}${Math.abs(r).toFixed(digits)}%`;
}

export function pctClass(p: number, digits = 1): string {
  const r = Number(p.toFixed(digits));
  return r < 0 ? 'neg' : r === 0 ? 'zero' : '';
}

export function fmtSol(n: number, digits = 3): string {
  const s = Math.abs(n).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  return n < 0 ? `${MINUS}${s}` : s;
}

export function fmtSignedSol(n: number, digits = 3): string {
  return n > 0 ? `+${fmtSol(n, digits)}` : fmtSol(n, digits);
}

export function fmtInt(n: number): string {
  return Math.round(n).toLocaleString('en-US');
}

export function ago(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 48) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

export function agoWords(ms: number): string {
  const m = Math.floor(Math.max(0, ms) / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m} min ago`;
  const h = Math.floor(m / 60);
  if (h < 48) return `${h} hr ago`;
  return `${Math.floor(h / 24)} days ago`;
}

export function until(ms: number): string {
  const m = Math.ceil(Math.max(0, ms) / 60000);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const r = m % 60;
  return r ? `${h} hr ${r} min` : `${h} hr`;
}

const WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty'];
export const numWord = (n: number) => WORDS[n] ?? String(n);

export const pad2 = (n: number) => String(n).padStart(2, '0');

export function clockTime(ms: number): string {
  return new Date(ms).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

export function dayTime(ms: number): string {
  return new Date(ms).toLocaleString('en-US', {
    weekday: 'short',
    hour: 'numeric',
    minute: '2-digit',
  });
}
