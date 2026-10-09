const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

/** Decode base58, or null if it contains characters outside the alphabet. */
export function base58Decode(s: string): Uint8Array | null {
  let zeros = 0;
  while (zeros < s.length && s[zeros] === '1') zeros++;
  // Little-endian base-256 digits of the value.
  const digits: number[] = [];
  for (const ch of s.slice(zeros)) {
    const v = ALPHABET.indexOf(ch);
    if (v < 0) return null;
    let carry = v;
    for (let i = 0; i < digits.length; i++) {
      carry += digits[i] * 58;
      digits[i] = carry & 0xff;
      carry >>= 8;
    }
    while (carry) {
      digits.push(carry & 0xff);
      carry >>= 8;
    }
  }
  const out = new Uint8Array(zeros + digits.length);
  for (let i = 0; i < digits.length; i++) out[zeros + i] = digits[digits.length - 1 - i];
  return out;
}

/** A Solana public address: base58 that decodes to exactly 32 bytes. */
export function isSolanaAddress(s: string): boolean {
  if (s.length < 32 || s.length > 44) return false;
  const b = base58Decode(s);
  return !!b && b.length === 32;
}
