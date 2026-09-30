import { lazy, Suspense, useEffect } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { FIRM_NAME } from '../firm.config';
import { Footer } from './components/Footer';
import { Header } from './components/Header';
import { TraderPanel } from './components/TraderPanel';
import { FirmProvider } from './hooks/useFirm';
import Home from './routes/Home';

const BooksPage = lazy(() => import('./routes/BooksPage'));
const Firm = lazy(() => import('./routes/Firm'));
const Hire = lazy(() => import('./routes/Hire'));
const Traders = lazy(() => import('./routes/Traders'));

const SpriteSheet = import.meta.env.DEV ? lazy(() => import('./routes/SpriteSheet')) : null;

const TITLES: Record<string, string> = {
  '/traders': 'the traders',
  '/firm': 'inside the firm',
  '/hire': 'hire a trader',
  '/books': 'the books',
};

function RouteEffects() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    const sub = TITLES[pathname];
    document.title = sub ? `${sub} · ${FIRM_NAME}` : FIRM_NAME;
  }, [pathname]);
  useEffect(() => {
    if (hash) {
      const el = document.getElementById(hash.slice(1));
      if (el) {
        el.scrollIntoView();
        return;
      }
    }
    window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}

function NotFound() {
  return (
    <div className="wrap page-head">
      <p className="label">404</p>
      <h1 className="hero-title">
        wrong floor.
        <em>try the lift.</em>
      </h1>
      <Link to="/" className="textlink">
        back to the lobby <span aria-hidden="true">→</span>
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <FirmProvider>
      <a href="#main" className="skip">
        Skip to content
      </a>
      <RouteEffects />
      <Header />
      <main id="main">
        <Suspense fallback={<div className="wrap page-head" aria-busy="true" />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/traders" element={<Traders />} />
            <Route path="/firm" element={<Firm />} />
            <Route path="/hire" element={<Hire />} />
            <Route path="/books" element={<BooksPage />} />
            {SpriteSheet && <Route path="/_sprites" element={<SpriteSheet />} />}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
      <TraderPanel />
    </FirmProvider>
  );
}
