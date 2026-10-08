import { useEffect, useState } from 'react';
import Dashboard from './components/Dashboard.jsx';
import { DataPage, HowItWorksPage, InvestigationsPage } from './components/SupportingPages.jsx';
import { Header } from './components/shared.jsx';

const pages = {
  '#monitoring': 'monitoring',
  '#investigations': 'investigations',
  '#how-it-works': 'how-it-works',
  '#methodology': 'methodology',
};

function App() {
  const [page, setPage] = useState(pages[window.location.hash] || 'monitoring');
  useEffect(() => {
    const syncPage = () => setPage(pages[window.location.hash] || 'monitoring');
    window.addEventListener('hashchange', syncPage);
    return () => window.removeEventListener('hashchange', syncPage);
  }, []);

  return <div className="app-shell">
    <Header page={page} />
    <div className="app-main"><main id="main-content" className="page-content">
      {page === 'monitoring' && <Dashboard />}
      {page === 'investigations' && <InvestigationsPage />}
      {page === 'how-it-works' && <HowItWorksPage />}
      {page === 'methodology' && <DataPage />}
    </main>
    <footer className="site-footer">
      <span>BURNBLIND <i>·</i> ENVIRONMENTAL INTELLIGENCE</span>
      <span>Replay detections are not confirmed incidents. <a href="https://www.openstreetmap.org/copyright">Map attribution</a></span>
    </footer></div>
  </div>;
}

export default App;
