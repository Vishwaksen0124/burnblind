import { Flame, Satellite } from 'lucide-react';

export function Header({ page }) {
  const links = [
    ['monitoring', '#monitoring', 'Monitoring'],
    ['investigations', '#investigations', 'Investigations'],
    ['how-it-works', page === 'home' ? '#landing-how-it-works' : '#how-it-works', 'How it works'],
    ['methodology', page === 'home' ? '#landing-methodology' : '#methodology', 'Documentation'],
  ];
  return <header className="landing-topbar">
    <a className="brand" href="#home" onClick={() => window.scrollTo(0, 0)} aria-label="BurnBlind home">
      <span className="brand-mark" aria-hidden="true"><Satellite className="brand-satellite" /><Flame className="brand-flame" /></span>
      <span className="brand-name">BURN<span>BLIND</span></span>
    </a>
    <nav className="landing-nav" aria-label="Primary navigation">
      <a href="#home" onClick={() => window.scrollTo(0, 0)} aria-current={page === 'home' ? 'page' : undefined}>Product</a>
      {links.map(([id, href, label]) => <a key={id} href={href} aria-current={page === id ? 'page' : undefined}>{label}</a>)}
    </nav>
    <span className="mode-badge"><i /> HISTORICAL REPLAY · 2025</span>
    <a className="landing-nav-cta" href="#monitoring">Explore monitoring <span aria-hidden="true">→</span></a>
  </header>;
}

export function Eyebrow({ children }) { return <p className="eyebrow">{children}</p>; }

export function PageHeading({ eyebrow, title, children, aside }) {
  return <section className="page-heading">
    <div><Eyebrow>{eyebrow}</Eyebrow><h1>{title}</h1>{children && <p className="page-lede">{children}</p>}</div>
    {aside && <div className="heading-aside">{aside}</div>}
  </section>;
}

export function StateMessage({ title, children, action }) {
  return <div className="state-message" role="status"><span className="state-rule" /><div><strong>{title}</strong><p>{children}</p>{action}</div></div>;
}
