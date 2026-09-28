import { useState } from 'react';
import { Books } from '../components/Books';
import { CACard } from '../components/CACard';
import { SinceLastVisit, YourCorner } from '../components/Corner';
import { DeskBoard } from '../components/DeskBoard';
import { Floors } from '../components/Floors';
import { Hero } from '../components/Hero';
import { Scene } from '../components/Scene';
import { Stats } from '../components/Stats';
import { StatusLine } from '../components/StatusLine';

export default function Home() {
  const [hot, setHot] = useState<number | null>(null);
  return (
    <div className="wrap">
      <div className="home-top">
        <div className="a-hero">
          <Hero />
          <CACard />
        </div>
        <div className="a-scene">
          <Scene hot={hot} onHover={setHot} />
        </div>
        <div className="a-status">
          <StatusLine />
          <Stats />
        </div>
        <div className="a-desks">
          <DeskBoard hot={hot} onHover={setHot} />
        </div>
      </div>
      <div className="home-grid">
        <div className="section">
          <Floors />
        </div>
        <div>
          <YourCorner />
          <SinceLastVisit />
        </div>
      </div>
      <div className="section section-heavy">
        <Books limit={8} />
      </div>
    </div>
  );
}
