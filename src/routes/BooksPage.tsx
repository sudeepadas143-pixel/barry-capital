import { PARTNER_NAME } from '../../firm.config';
import { Books } from '../components/Books';

export default function BooksPage() {
  return (
    <div className="wrap">
      <header className="page-head">
        <p className="label">The books</p>
        <h1 className="hero-title">
          every trade,
          <em>written down.</em>
        </h1>
        <p className="prose">
          Every trade the desks have made, with a note on why and the rule behind it. {PARTNER_NAME} reads all of it.
        </p>
      </header>
      <Books showHead={false} filters />
    </div>
  );
}
