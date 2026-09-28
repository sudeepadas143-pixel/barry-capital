import { Link } from 'react-router-dom';
import { FIRM_NAME, X_URL } from '../../firm.config';
import { FOOTER_NOTE } from '../copy';
import { XIcon } from './Icons';

export function Footer() {
  return (
    <footer className="footer">
      <div className="wrap footer-in">
        <span className="brand-name">{FIRM_NAME}</span>
        <nav aria-label="Footer">
          <Link to="/traders">traders</Link>
          <Link to="/firm">floors</Link>
          <Link to="/books">books</Link>
          <a href={X_URL} target="_blank" rel="noreferrer" aria-label="X">
            <XIcon size={16} />
          </a>
        </nav>
        <p className="footer-small">{FOOTER_NOTE}</p>
      </div>
    </footer>
  );
}
