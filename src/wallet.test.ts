import { describe, expect, it } from 'vitest';
import { base58Decode, checkWallet, traderFromWallet } from './wallet';

describe('wallet addresses', () => {
  it('decodes real Solana addresses to 32 bytes', () => {
    expect(base58Decode('11111111111111111111111111111111')?.length).toBe(32);
    expect(base58Decode('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')?.length).toBe(32);
    expect(base58Decode('So11111111111111111111111111111111111111112')?.length).toBe(32);
  });

  it('accepts a public address and trims it', () => {
    expect(checkWallet('  TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA ')).toEqual({ kind: 'ok', address: 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA' });
  });

  it('rejects things that are not addresses', () => {
    expect(checkWallet('0xabc').kind).toBe('invalid');
    expect(checkWallet('hello there').kind).toBe('invalid');
    expect(checkWallet('abc').kind).toBe('invalid');
  });

  it('refuses recovery phrases and private keys', () => {
    expect(checkWallet('abandon '.repeat(11) + 'about').kind).toBe('secret');
    expect(checkWallet(`[${Array.from({ length: 64 }, (_, i) => i).join(',')}]`).kind).toBe('secret');
    // A 64-byte key in base58 is about 88 characters.
    expect(checkWallet('5' + 'K'.repeat(87)).kind).toBe('secret');
  });

  it('always makes the same trader from the same wallet', () => {
    const a = traderFromWallet('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');
    const b = traderFromWallet('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');
    const c = traderFromWallet('So11111111111111111111111111111111111111112');
    expect(a).toEqual(b);
    expect(a.seed).not.toBe(c.seed);
  });
});
