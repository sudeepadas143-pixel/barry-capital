/**
 * Listens to the token's chat on pump.fun. This is the same chat server the
 * pump.fun site uses (socket.io at wss://livechat.pump.fun); reading it needs
 * no login. It isn't a documented public API, so if pump.fun changes it the
 * bot logs loudly and stops minting rather than guessing.
 *
 * On every (re)connect it also reads the last 50 messages, so comments posted
 * while the bot was down are still picked up.
 */
import { io, type Socket } from 'socket.io-client';
import { env } from './env.js';
import { enqueue, type Comment } from './airdrop.js';

export interface WatchState {
  connected: boolean;
  lastEventAt: number;
  lastMessageAt: number;
  seen: number;
}

export function watch(): WatchState {
  const state: WatchState = { connected: false, lastEventAt: 0, lastMessageAt: 0, seen: 0 };
  const room = env.tokenMint();
  const s: Socket = io(env.chatUrl(), {
    transports: ['websocket'],
    extraHeaders: { Origin: 'https://pump.fun' },
    reconnection: true,
    reconnectionDelay: 2000,
    reconnectionDelayMax: 30_000,
  });

  const take = (m: Comment) => {
    state.seen++;
    state.lastMessageAt = Date.now();
    enqueue(m);
  };

  s.on('connect', () => {
    state.connected = true;
    console.log(`chat: connected, joining ${room}`);
    s.emit('joinRoom', { roomId: room, username: '' }, () => {
      s.emit('getMessageHistory', { roomId: room, before: null, limit: 50 }, (res: Comment[] | { messages?: Comment[] }) => {
        const list = Array.isArray(res) ? res : res?.messages ?? [];
        console.log(`chat: backfilled ${list.length} recent messages`);
        for (const m of list.slice().reverse()) take(m);
      });
    });
  });
  s.on('disconnect', (why) => {
    state.connected = false;
    console.warn(`chat: disconnected (${why}), reconnecting`);
  });
  s.on('connect_error', (e) => console.warn(`chat: connect error: ${e.message}`));
  s.on('newMessage', (m: Comment) => take(m));
  s.onAny(() => {
    state.lastEventAt = Date.now();
  });
  return state;
}
