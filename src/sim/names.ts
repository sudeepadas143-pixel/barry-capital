/**
 * Trader surnames are ordinary and generic, not references to anyone. Coin
 * tickers are real Solana memecoins; their prices here are not.
 */

export const STARTING_ROSTER = [
  ['whitlock', 'permabull'],
  ['osei', 'trend'],
  ['castellano', 'dip'],
  ['lindqvist', 'sniper'],
  ['marsh', 'diamond'],
  ['adebayo', 'fiver'],
  ['varga', 'intern'],
  ['halloran', 'quant'],
  ['beaumont', 'stops'],
  ['rourke', 'narrative'],
  ['tanaka', 'averager'],
] as const;

export const SURNAMES = [
  'pryce', 'mendes', 'frost', 'okafor', 'delacroix', 'nakamura', 'brennan', 'hale', 'sorensen', 'quintero',
  'abernathy', 'kowalski', 'fairweather', 'moreau', 'iqbal', 'duarte', 'thackeray', 'olsen', 'mbeki', 'ashby',
  'castillo', 'haddad', 'pemberton', 'novak', 'achebe', 'kingsley', 'rahman', 'oduya', 'fennimore', 'bianchi',
  'harrow', 'lucero', 'albright', 'petrov', 'mcallister', 'yoon', 'sandoval', 'whitcombe', 'grieve', 'amadi',
  'holloway', 'ferreira', 'stroud', 'kimura', 'baptiste', 'lachance', 'oyelaran', 'dunmore', 'szabo', 'carver',
  'ellison', 'navarro', 'trent', 'boateng', 'lindgren', 'mercer', 'vasquez', 'aldridge', 'sato', 'kerrigan',
  'fontaine', 'adeyemi', 'harlow', 'costa', 'winslow', 'rasmussen', 'bello', 'crane', 'ivanova', 'prentice',
  'galloway', 'moretti', 'hartley', 'nwosu', 'blackwood', 'eriksen', 'salazar', 'penrose', 'takahashi', 'mulligan',
  'ashworth', 'delgado', 'onyango', 'redgrave', 'kapoor', 'lowell', 'marchetti', 'obi', 'hollis', 'strand',
];

export type Theme = 'dogs' | 'cats' | 'critters' | 'agents' | 'culture';
export const THEMES: Theme[] = ['dogs', 'cats', 'critters', 'agents', 'culture'];
export const THEME_LABEL: Record<Theme, string> = {
  dogs: 'dog coins',
  cats: 'cat coins',
  critters: 'other animals',
  agents: 'agent coins',
  culture: 'internet culture',
};

/**
 * Real Solana memecoins the desks watch. Only the tickers and names are real:
 * every price, chart and trade on the site is made up. Coins named after real
 * people are left out on purpose.
 */
export const COINS: { ticker: string; name: string; theme: Theme }[] = [
  { ticker: 'BONK', name: 'Bonk', theme: 'dogs' },
  { ticker: 'WIF', name: 'dogwifhat', theme: 'dogs' },
  { ticker: 'DOG', name: 'Dog', theme: 'dogs' },
  { ticker: 'SAMO', name: 'Samoyedcoin', theme: 'dogs' },
  { ticker: 'BERT', name: 'Bertram the Pomeranian', theme: 'dogs' },
  { ticker: 'MYRO', name: 'Myro', theme: 'dogs' },
  { ticker: 'POPCAT', name: 'Popcat', theme: 'cats' },
  { ticker: 'MEW', name: 'cat in a dogs world', theme: 'cats' },
  { ticker: 'MICHI', name: 'michi', theme: 'cats' },
  { ticker: 'PENGU', name: 'Pudgy Penguins', theme: 'critters' },
  { ticker: 'PNUT', name: 'Peanut the Squirrel', theme: 'critters' },
  { ticker: 'MOODENG', name: 'Moo Deng', theme: 'critters' },
  { ticker: 'FWOG', name: 'Fwog', theme: 'critters' },
  { ticker: 'PONKE', name: 'Ponke', theme: 'critters' },
  { ticker: 'SLERF', name: 'Slerf', theme: 'critters' },
  { ticker: 'GOAT', name: 'Goatseus Maximus', theme: 'agents' },
  { ticker: 'ZEREBRO', name: 'Zerebro', theme: 'agents' },
  { ticker: 'ACT', name: 'Act I', theme: 'agents' },
  { ticker: 'PIPPIN', name: 'Pippin', theme: 'agents' },
  { ticker: 'FARTCOIN', name: 'Fartcoin', theme: 'agents' },
  { ticker: 'USELESS', name: 'Useless Coin', theme: 'culture' },
  { ticker: 'GIGA', name: 'Gigachad', theme: 'culture' },
  { ticker: 'VINE', name: 'Vine', theme: 'culture' },
  { ticker: 'UFD', name: 'Unicorn Fart Dust', theme: 'culture' },
  { ticker: 'CHILLHOUSE', name: 'Chill House', theme: 'culture' },
  { ticker: 'CHILLGUY', name: 'Just a chill guy', theme: 'culture' },
  { ticker: 'SIGMA', name: 'Sigma', theme: 'culture' },
  { ticker: 'NOBODY', name: 'Nobody Sausage', theme: 'culture' },
  { ticker: 'USDUC', name: 'Unstable Coin', theme: 'culture' },
  { ticker: 'BOME', name: 'Book of Meme', theme: 'culture' },
  { ticker: 'PEPECOIN', name: 'PepeCoin', theme: 'culture' },
];

export const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
