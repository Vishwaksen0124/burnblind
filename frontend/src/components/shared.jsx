export function Header({ page }) {
  const links = [
    ['monitoring', '#monitoring', 'Monitoring'],
    ['investigations', '#investigations', 'Investigations'],
    ['how-it-works', '#how-it-works', 'How it works'],
    ['methodology', '#methodology', 'Data & methodology'],
  ];
  return <header className="topbar">
    <a className="brand" href="#monitoring" aria-label="BurnBlind monitoring home">
      <span className="brand-mark" aria-hidden="true"><span /></span>
      <span className="brand-name">BURN<span>BLIND</span></span>
    </a>
    <nav className="primary-nav" aria-label="Primary navigation">
      {links.map(([id, href, label]) => <a key={id} href={href} aria-current={page === id ? 'page' : undefined}>{label}</a>)}
    </nav>
    <span className="mode-badge"><i /> HISTORICAL REPLAY · 2025</span>
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
