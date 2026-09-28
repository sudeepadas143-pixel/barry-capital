/**
 * A 3x5 pixel font for plaques, the lobby ticker and desk numbers.
 * Each glyph is five rows of three bits, top to bottom.
 */
const G: Record<string, number[]> = {
  A: [2, 5, 7, 5, 5], B: [6, 5, 6, 5, 6], C: [3, 4, 4, 4, 3], D: [6, 5, 5, 5, 6], E: [7, 4, 6, 4, 7],
  F: [7, 4, 6, 4, 4], G: [3, 4, 5, 5, 3], H: [5, 5, 7, 5, 5], I: [7, 2, 2, 2, 7], J: [1, 1, 1, 5, 2],
  K: [5, 5, 6, 5, 5], L: [4, 4, 4, 4, 7], M: [5, 7, 7, 5, 5], N: [6, 5, 5, 5, 5], O: [2, 5, 5, 5, 2],
  P: [6, 5, 6, 4, 4], Q: [2, 5, 5, 6, 3], R: [6, 5, 6, 5, 5], S: [3, 4, 2, 1, 6], T: [7, 2, 2, 2, 2],
  U: [5, 5, 5, 5, 7], V: [5, 5, 5, 5, 2], W: [5, 5, 7, 7, 5], X: [5, 5, 2, 5, 5], Y: [5, 5, 2, 2, 2],
  Z: [7, 1, 2, 4, 7],
  '0': [7, 5, 5, 5, 7], '1': [2, 6, 2, 2, 7], '2': [6, 1, 2, 4, 7], '3': [6, 1, 2, 1, 6], '4': [5, 5, 7, 1, 1],
  '5': [7, 4, 6, 1, 6], '6': [3, 4, 7, 5, 7], '7': [7, 1, 2, 2, 2], '8': [7, 5, 7, 5, 7], '9': [7, 5, 7, 1, 6],
  '+': [0, 2, 7, 2, 0], '-': [0, 0, 7, 0, 0], '%': [5, 1, 2, 4, 5], '.': [0, 0, 0, 0, 2], '$': [3, 6, 2, 3, 6],
  ' ': [0, 0, 0, 0, 0], '^': [2, 7, 0, 0, 0], v: [0, 0, 0, 7, 2], ':': [0, 2, 0, 2, 0], '/': [1, 1, 2, 4, 4],
  '&': [2, 5, 2, 5, 3],
};

export function glyph(ch: string): number[] {
  return G[ch] ?? G[ch.toUpperCase()] ?? G[' '];
}

/** Width in pixels of a string at 3px glyphs with 1px spacing. */
export const textWidth = (s: string) => Math.max(0, s.length * 4 - 1);

/** Draw text by calling `plot(x, y)` for each lit pixel, from a top-left origin. */
export function drawText(s: string, plot: (x: number, y: number) => void) {
  let cx = 0;
  for (const ch of s) {
    const g = glyph(ch);
    for (let r = 0; r < 5; r++) for (let b = 0; b < 3; b++) if (g[r] & (4 >> b)) plot(cx + b, r);
    cx += 4;
  }
}
