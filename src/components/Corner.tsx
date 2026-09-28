import { Link } from 'react-router-dom';
import { CORNER, SINCE } from '../copy';

export function YourCorner() {
  return (
    <section className="section corner" aria-labelledby="corner-title">
      <p className="label">{CORNER.label}</p>
      <h2 id="corner-title" className="display">
        {CORNER.title}
      </h2>
      <Link to="/hire" className="textlink">
        {CORNER.link} <span aria-hidden="true">→</span>
      </Link>
      <p className="prose">{CORNER.body}</p>
    </section>
  );
}

export function SinceLastVisit() {
  const followed = 0;
  return (
    <section className="section since" aria-labelledby="since-title">
      <div className="since-head">
        <h2 id="since-title" className="label">
          {SINCE.label}
        </h2>
        <Link to="/traders" className="textlink">
          {followed} followed
        </Link>
      </div>
      <p className="prose">{SINCE.empty}</p>
    </section>
  );
}
