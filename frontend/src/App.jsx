import { useEffect, useState } from 'react';
import Dashboard from './components/Dashboard.jsx';
import ProductPage from './components/ProductPage.jsx';
import { DataPage, HowItWorksPage, InvestigationsPage } from './components/SupportingPages.jsx';
import ReplayPage from './components/ReplayPage.jsx';
import { Header } from './components/shared.jsx';
import { ReviewerAuthProvider } from './reviewerAuth.jsx';

const pages = {
  '#home': 'home',
  '#monitoring': 'monitoring',
  '#replay': 'replay',
  '#investigations': 'investigations',
  '#how-it-works': 'how-it-works',
  '#methodology': 'methodology',
};

function App() {
  return <ReviewerAuthProvider><Application /></ReviewerAuthProvider>;
}

function Application() {
  const [page, setPage] = useState(pages[window.location.hash] || 'home');
  useEffect(() => {
    const syncPage = () => {
      const nextPage = pages[window.location.hash] || 'home';
      setPage(nextPage);
    };
    window.addEventListener('hashchange', syncPage);
    return () => window.removeEventListener('hashchange', syncPage);
  }, []);
  useEffect(() => { window.scrollTo(0, 0); }, [page]);

  return <div className="app-shell">
    <Header page={page} />
    <div className="app-main"><main id="main-content" className="page-content">
      {page === 'monitoring' && <Dashboard />}
      {page === 'replay' && <ReplayPage />}
      {page === 'home' && <ProductPage />}
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
