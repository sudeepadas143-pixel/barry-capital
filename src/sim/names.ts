/**
 * Invented names only. Trader surnames are ordinary and generic; coin names are
 * word combinations, deliberately avoiding any well-known real token.
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

export type Theme = 'animal' | 'food' | 'weather' | 'office' | 'household';
export const THEMES: Theme[] = ['animal', 'food', 'weather', 'office', 'household'];
export const THEME_LABEL: Record<Theme, string> = {
  animal: 'animals',
  food: 'food',
  weather: 'weather',
  office: 'office supplies',
  household: 'things in a drawer',
};

export const NOUNS: Record<Theme, string[]> = {
  animal: ['goose', 'toad', 'moth', 'newt', 'crab', 'otter', 'badger', 'heron', 'snail', 'pigeon', 'hamster', 'walrus', 'eel', 'llama', 'sloth', 'gecko', 'beetle', 'possum', 'ferret', 'puffin', 'mole', 'tapir', 'yak', 'lobster'],
  food: ['loaf', 'gravy', 'crumb', 'beans', 'pickle', 'waffle', 'noodle', 'toast', 'custard', 'biscuit', 'soup', 'prawn', 'muffin', 'turnip', 'crouton', 'scone', 'relish', 'dumpling', 'kipper', 'trifle'],
  weather: ['drizzle', 'fog', 'sleet', 'puddle', 'gust', 'hail', 'mist', 'squall', 'monsoon', 'breeze', 'frost', 'rainbow', 'cloud', 'dew'],
  office: ['stapler', 'memo', 'binder', 'fax', 'lanyard', 'toner', 'inkjet', 'folder', 'postit', 'rolodex', 'shredder', 'swivel', 'cubicle', 'ledger'],
  household: ['sock', 'spoon', 'bucket', 'slipper', 'kazoo', 'kettle', 'spork', 'doily', 'teapot', 'mop', 'button', 'thimble', 'candle', 'hanger', 'sponge', 'plunger'],
};

export const ADJECTIVES = [
  'damp', 'tiny', 'big', 'lil', 'grumpy', 'sleepy', 'loyal', 'brave', 'honest', 'soggy', 'gentle', 'frank',
  'humble', 'silent', 'legal', 'certified', 'retired', 'local', 'spare', 'quiet', 'official', 'senior', 'wet',
  'baby', 'king', 'sir', 'captain', 'lucky', 'wobbly', 'chunky', 'polite', 'moist', 'haunted', 'vintage',
];

export const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
