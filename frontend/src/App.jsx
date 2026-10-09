import { useEffect, useState } from 'react';
import Dashboard from './components/Dashboard.jsx';
import ProductPage from './components/ProductPage.jsx';
import { DataPage, HowItWorksPage, InvestigationsPage } from './components/SupportingPages.jsx';
import ReplayPage from './components/ReplayPage.jsx';
import { Header, PageHeading, StateMessage } from './components/shared.jsx';
import { ReviewerAuthProvider } from './reviewerAuth.jsx';
import { getEvent } from './api.js';
import EventDetail from './components/EventDetail.jsx';

const pages = {
  '#home': 'home',
  '#monitoring': 'monitoring',
  '#replay': 'replay',
  '#investigations': 'investigations',
  '#how-it-works': 'how-it-works',
  '#methodology': 'methodology',
};

function currentRoute() {
  const hash = window.location.hash;
  const match = hash.match(/^#investigations\/(evt_[A-Fa-f0-9]{24})$/);
  return { page: match ? 'event-review' : (pages[hash] || 'home'), eventId: match?.[1] || null };
}

function App() {
  return <ReviewerAuthProvider><Application /></ReviewerAuthProvider>;
}

function Application() {
  const [route, setRoute] = useState(currentRoute);
  useEffect(() => {
    const syncPage = () => {
      setRoute(currentRoute());
    };
    window.addEventListener('hashchange', syncPage);
    return () => window.removeEventListener('hashchange', syncPage);
  }, []);
  useEffect(() => { window.scrollTo(0, 0); }, [route.page, route.eventId]);

  return <div className="app-shell">
    <Header page={route.page === 'event-review' ? 'investigations' : route.page} />
    <div className="app-main"><main id="main-content" className="page-content">
      {route.page === 'monitoring' && <Dashboard />}
      {route.page === 'replay' && <ReplayPage />}
      {route.page === 'home' && <ProductPage />}
      {route.page === 'investigations' && <InvestigationsPage />}
      {route.page === 'event-review' && <EventReviewPage eventId={route.eventId} />}
      {route.page === 'how-it-works' && <HowItWorksPage />}
      {route.page === 'methodology' && <DataPage />}
    </main>
    <footer className="site-footer">
      <span>BURNBLIND <i>·</i> ENVIRONMENTAL INTELLIGENCE</span>
      <span>Replay detections are not confirmed incidents. <a href="https://www.openstreetmap.org/copyright">Map attribution</a></span>
    </footer></div>
  </div>;
}

function EventReviewPage({ eventId }) {
  const [event, setEvent] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    getEvent(eventId, controller.signal).then(setEvent).catch((cause) => {
      if (cause.name !== 'AbortError') setError(cause.message || 'Candidate details are unavailable.');
    });
    return () => controller.abort();
  }, [eventId]);

  if (error) return <><PageHeading eyebrow="HUMAN REVIEW" title="Candidate review"><a className="text-button" href="#investigations">Back to investigations</a></PageHeading><StateMessage title="Candidate unavailable">{error}</StateMessage></>;
  if (!event) return <><PageHeading eyebrow="HUMAN REVIEW" title="Candidate review">Loading candidate and investigation records.</PageHeading><StateMessage title="Loading candidate">Reading the selected event.</StateMessage></>;
  return <>
    <PageHeading eyebrow="HUMAN REVIEW · DEDICATED EVENT RECORD" title="Candidate review"><a className="text-button" href="#investigations">← Back to investigations</a></PageHeading>
    <EventDetail event={event} initialTab="investigation" onClose={() => { window.location.hash = '#investigations'; }} />
  </>;
}

export default App;
