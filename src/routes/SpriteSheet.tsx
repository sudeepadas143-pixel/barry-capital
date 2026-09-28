import { Headshot } from '../components/Sprite';
import { PARTNER_LOOK } from '../art/partner';

/** Dev-only contact sheet for checking sprite art. Not linked or built into production routes. */
export default function SpriteSheet() {
  const looks = Array.from({ length: 24 }, (_, i) => ({
    skin: i % 6,
    hair: (i * 3) % 7,
    hairStyle: i % 4,
    suit: (i * 5) % 6,
    tie: (i * 7) % 6,
  }));
  return (
    <div className="wrap" style={{ padding: 24 }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
        <Headshot look={PARTNER_LOOK} glasses size={128} />
        {looks.map((l, i) => (
          <Headshot key={i} look={l} size={96} />
        ))}
      </div>
    </div>
  );
}
