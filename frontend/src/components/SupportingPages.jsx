import { useEffect, useState } from 'react';
import { getInvestigations } from '../api.js';
import { PageHeading, StateMessage } from './shared.jsx';

const PIPELINE = [
  ['01', 'Observe', 'Collect satellite and environmental observations with source and time metadata.'],
  ['02', 'Find monitoring gaps', 'Identify periods and places where observation coverage is incomplete or uncertain.'],
  ['03', 'Detect', 'Group potential thermal observations into candidate events. A detection is not ground truth.'],
  ['04', 'Assess impact', 'Estimate potential downwind exposure when weather and population inputs are available.'],
  ['05', 'Prioritize', 'Combine validated evidence, monitoring blindness, and impact to rank events.'],
  ['06', 'Investigate', 'Cross-check important or uncertain events and present evidence for human review.'],
];

export function HowItWorksPage() {
  return <>
    <PageHeading eyebrow="SYSTEM OVERVIEW" title="How BurnBlind works">A transparent workflow for finding potential events that deserve a closer look.</PageHeading>
    <section className="pipeline" aria-label="BurnBlind monitoring pipeline">{PIPELINE.map(([number, title, copy]) => <article className="pipeline-step" key={number}><span className="pipeline-number">{number}</span><div><h2>{title}</h2><p>{copy}</p></div><span className="pipeline-arrow" aria-hidden="true">↘</span></article>)}</section>
    <p className="science-note"><strong>Scientific boundary</strong> BurnBlind identifies potential monitoring gaps and cross-source differences. It does not claim a confirmed fire without independent ground truth.</p>
  </>;
}

export const SOURCES = [
  { name: 'GK2A AMI', url: 'https://zenodo.org/records/20084790', type: 'Historical replay source', provides: 'Thermal hotspot detections used to build the current Punjab and Haryana replay sample.', limit: 'A satellite detection is a candidate observation, not a verified incident. Current UI sample covers Oct–Nov 2025.' },
  { name: 'NASA FIRMS / VIIRS', url: 'https://firms.modaps.eosdis.nasa.gov/active_fire/', type: 'Planned comparison source', provides: 'Independent active-fire observations for cross-sensor comparison.', limit: 'No matched comparison records are currently exposed by the application API.' },
  { name: 'Weather / reanalysis', url: 'https://open-meteo.com/en/docs/historical-weather-api', type: 'Planned environmental source', provides: 'Wind context for estimating a potential downwind screening corridor.', limit: 'Weather evidence is not yet connected to the dashboard API.' },
  { name: 'WorldPop', url: 'https://www.worldpop.org/', type: 'Planned exposure source', provides: 'Population estimates that may support potential exposure screening.', limit: 'No population exposure estimate is currently available in the replay API.' },
];

export function DataPage() {
  return <>
    <PageHeading eyebrow="TRANSPARENCY" title="Data & methodology">Understand what the current replay can show, what it cannot, and how future assessments will be grounded.</PageHeading>
    <section className="source-grid" aria-label="Data sources">{SOURCES.map((source) => <article className="source-card panel" key={source.name}><span className="source-type">{source.type}</span><h2><a href={source.url} target="_blank" rel="noreferrer">{source.name}<span aria-hidden="true"> ↗</span></a></h2><p>{source.provides}</p><div className="source-limit"><strong>LIMITATION</strong><p>{source.limit}</p></div></article>)}</section>
    <section className="terms-panel panel"><p className="eyebrow">TERMINOLOGY</p><div className="terms-accordion">
      <details><summary>Monitoring blind spot</summary><p>A gap or limitation in observation coverage; it does not prove an event occurred.</p></details>
      <details><summary>Cross-sensor disagreement</summary><p>Different sensors report different observations or coverage. This is evidence to investigate, not proof that a sensor missed a fire.</p></details>
      <details><summary>Potential fire event</summary><p>A candidate grouped from source detections. Confirmation requires independent ground truth.</p></details>
      <details><summary>Estimated exposure</summary><p>A modeled estimate that depends on population and environmental inputs; it is not a measured impact.</p></details>
    </div></section>
  </>;
}

export function InvestigationsPage() {
  const [items, setItems] = useState([]);
  const [nextCursor, setNextCursor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setItems([]);
    setNextCursor(null);
    getInvestigations(controller.signal)
      .then((page) => { setItems(page.items || []); setNextCursor(page.next_cursor || null); })
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [retry]);

  async function loadMore() {
    if (!nextCursor || loadingMore) return;
    const controller = new AbortController();
    setLoadingMore(true);
    try {
      const page = await getInvestigations(controller.signal, 50, nextCursor);
      setItems((current) => [...current, ...(page.items || [])]);
      setNextCursor(page.next_cursor || null);
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message);
    } finally {
      setLoadingMore(false);
    }
  }

  return <>
    <PageHeading eyebrow="EVIDENCE REVIEW" title="Investigations">Queued and completed evidence reviews, linked to their candidate event records.</PageHeading>
    {loading && <StateMessage title="Loading investigations">Reading persisted review records.</StateMessage>}
    {error && !loading && <StateMessage title="Investigation data unavailable">{error} <button className="text-button" onClick={() => setRetry((value) => value + 1)}>Retry</button></StateMessage>}
    {!loading && !error && items.length === 0 && <StateMessage title="No investigations yet">Request an investigation from a candidate event. Completed reports will appear here.</StateMessage>}
    {!loading && !error && items.length > 0 && <section className="investigation-list" aria-label="Investigation reports">
      {items.map((item) => <article className="investigation-card panel" key={item.event_id}>
        <header><div><p className="eyebrow">EVENT · {item.event_id}</p><h2>{item.investigation?.classification?.replaceAll('_', ' ') || item.status?.replaceAll('_', ' ')}</h2></div><span className={`investigation-status status-${item.status?.toLowerCase()}`}>{item.status?.replaceAll('_', ' ')}</span></header>
        {item.investigation?.summary && <p className="investigation-card-summary">{item.investigation.summary}</p>}
        {item.investigation?.evidence?.length > 0 && <p className="investigation-card-meta">{item.investigation.evidence.length} cited evidence {item.investigation.evidence.length === 1 ? 'record' : 'records'} · {item.investigation.recommended_action?.replaceAll('_', ' ')}</p>}
        {item.error_code && <p className="report-error">Review failed · {item.error_code}</p>}
        <footer><span>Requested {formatDate(item.requested_at_utc)}</span>{item.completed_at_utc && <span>Completed {formatDate(item.completed_at_utc)}</span>}<span>{item.model_id || 'Model metadata unavailable'}</span></footer>
      </article>)}
      {nextCursor && <button className="action-button investigation-load-more" disabled={loadingMore} onClick={loadMore}>{loadingMore ? 'Loading…' : 'Load more investigations'}</button>}
    </section>}
  </>;
}

function formatDate(value) {
  if (!value) return 'time unavailable';
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? 'time unavailable' : date.toLocaleString();
}
