import { Flame, Menu, Satellite, X } from 'lucide-react';
import { useState } from 'react';
import { useReviewerAuth } from '../reviewerAuth.jsx';

export function Header({ page }) {
  const reviewerAuth = useReviewerAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const links = [
    ['monitoring', '#monitoring', 'Monitoring'],
    ['replay', '#replay', 'Replay'],
    ['investigations', '#investigations', 'Investigations'],
    ['how-it-works', page === 'home' ? '#landing-how-it-works' : '#how-it-works', 'How it works'],
    ['methodology', page === 'home' ? '#landing-methodology' : '#methodology', 'Documentation'],
  ];
  return <header className="landing-topbar" data-menu-open={menuOpen}>
    <a className="brand" href="#home" onClick={() => window.scrollTo(0, 0)} aria-label="BurnBlind home">
      <span className="brand-mark" aria-hidden="true"><Satellite className="brand-satellite" /><Flame className="brand-flame" /></span>
      <span className="brand-name">BURN<span>BLIND</span></span>
    </a>
    <nav className="landing-nav" id="primary-navigation" aria-label="Primary navigation">
      <a href="#home" onClick={() => { window.scrollTo(0, 0); setMenuOpen(false); }} aria-current={page === 'home' ? 'page' : undefined}>Product</a>
      {links.map(([id, href, label]) => <a key={id} href={href} aria-current={page === id ? 'page' : undefined} onClick={() => setMenuOpen(false)}>{label}</a>)}
    </nav>
    <span className="mode-badge"><i /> HISTORICAL REPLAY · 2025</span>
    {reviewerAuth.session
      ? <button className="reviewer-access" onClick={() => reviewerAuth.signOut().catch(() => {})} title={reviewerAuth.session.email}>Sign out</button>
      : <button className="reviewer-access" onClick={() => reviewerAuth.openSignIn()}>Reviewer sign in</button>}
    <button className="navigation-toggle" type="button" aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={menuOpen} aria-controls="primary-navigation" onClick={() => setMenuOpen((open) => !open)}>
      {menuOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
    </button>
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
