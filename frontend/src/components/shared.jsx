export function Header({ page }) {
  const links = [
    ['monitoring', '#monitoring', 'Live monitoring', '⌖'],
    ['investigations', '#investigations', 'Investigations', '◉'],
    ['how-it-works', '#how-it-works', 'How it works', '⌁'],
    ['methodology', '#methodology', 'Data & methodology', '▤'],
  ];
  return <header className="side-rail">
    <a className="brand" href="#monitoring" aria-label="BurnBlind monitoring home">
      <span className="brand-mark" aria-hidden="true"><span /></span>
      <span className="brand-name">BURN<span>BLIND</span></span>
    </a>
    <nav className="primary-nav" aria-label="Primary navigation">
      {links.map(([id, href, label, icon]) => <a key={id} href={href} aria-current={page === id ? 'page' : undefined}><span className="nav-icon" aria-hidden="true">{icon}</span><span>{label}</span></a>)}
    </nav>
    <div className="rail-foot"><span className="mode-badge"><i /> HISTORICAL REPLAY · 2025</span><small>Punjab & Haryana<br />Environmental intelligence</small></div>
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
