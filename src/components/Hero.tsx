import { Link } from 'react-router-dom';
import { HERO } from '../copy';

export function Hero() {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <p className="label">
        {HERO.kicker[0]} · <strong>{HERO.kicker[1]}</strong>
      </p>
      <h1 id="hero-title" className="hero-title">
        {HERO.lead}
        <em>{HERO.accent}</em>
      </h1>
      <p className="prose">{HERO.body}</p>
      <div className="hero-cta">
        <Link to="/hire" className="btn-black">
          {HERO.cta} <span aria-hidden="true">↗</span>
        </Link>
        <Link to="/traders" className="textlink">
          {HERO.secondary} <span className="arr" aria-hidden="true">→</span>
        </Link>
      </div>
    </section>
  );
}
