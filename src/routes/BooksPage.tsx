import { PARTNER_NAME } from '../../firm.config';
import { Books } from '../components/Books';

export default function BooksPage() {
  return (
    <div className="wrap">
      <header className="page-head">
        <p className="label">The books</p>
        <h1 className="hero-title">
          every trade,
          <em>in pencil.</em>
        </h1>
        <p className="prose">
          The full notebook. Each entry carries the reason given at the time and the rule it was filed under.{' '}
          {PARTNER_NAME} reads all of it.
        </p>
      </header>
      <Books showHead={false} filters />
    </div>
  );
}
