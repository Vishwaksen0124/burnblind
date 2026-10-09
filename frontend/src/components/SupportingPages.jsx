import { useEffect, useState } from 'react';
import { getInvestigations } from '../api.js';
import { PageHeading, StateMessage } from './shared.jsx';

const PIPELINE = [
  { number: '01', title: 'Observe', copy: 'Start with a source record and preserve its timestamp, coordinates, sensor and provenance.', input: 'GK2A AMI historical replay', result: 'Normalized observations in UTC and a shared 5 km grid', state: 'Active in replay' },
  { number: '02', title: 'Group candidates', copy: 'Nearby records are grouped only within the configured grid and time window; stable IDs keep an event traceable.', input: 'Validated observations', result: 'One candidate event with its linked source records', state: 'Active in replay' },
  { number: '03', title: 'Assess coverage', copy: 'Coverage, data quality and history can add context when sourced records exist. Missing records stay unavailable.', input: 'Coverage and historical records', result: 'Blindness and historical features, when available', state: 'Inputs incomplete in replay' },
  { number: '04', title: 'Compare and estimate', copy: 'Independent sensor matches, event-hour weather and population estimates remain separately sourced and labeled.', input: 'Matched detections, ERA5 and WorldPop', result: 'Comparison and potential exposure with limitations', state: 'Per-event availability' },
  { number: '05', title: 'Triage', copy: 'Versioned deterministic rules rank only events with the required feature inputs. Missing values do not become zero.', input: 'Validated score features', result: 'Priority and a recorded qualification reason', state: 'Seed events currently unscored' },
  { number: '06', title: 'Investigate', copy: 'A selected or qualifying event gets one bounded evidence packet. Strands uses the configured DeepSeek provider to produce a structured report.', input: 'One event and its assembled evidence packet', result: 'Cited findings, uncertainty and a human-review recommendation', state: 'Live path verified · 09 Oct 2026' },
  { number: '07', title: 'Review and learn', copy: 'A person records an outcome against the candidate; replay and evaluation keep the result auditable.', input: 'Investigation report and reviewer decision', result: 'Append-only human outcome for later evaluation', state: 'Review flow implemented' },
];

export function HowItWorksPage() {
  return <>
    <PageHeading eyebrow="SYSTEM OVERVIEW" title="How BurnBlind works">A transparent workflow for finding potential events that deserve a closer look.</PageHeading>
    <section className="pipeline" aria-label="BurnBlind monitoring pipeline">{PIPELINE.map(({ number, title, copy, input, result, state }) => <article className="pipeline-step" key={number}><span className="pipeline-number">{number}</span><div className="pipeline-main"><h2>{title}</h2><p>{copy}</p><div className="pipeline-io"><p><span>INPUT</span>{input}</p><p><span>OUTPUT</span>{result}</p></div></div><span className="pipeline-state">{state}</span></article>)}</section>
    <p className="science-note"><strong>Scientific boundary</strong> BurnBlind identifies potential monitoring gaps and cross-source differences. It does not claim a confirmed fire without independent ground truth.</p>
  </>;
}

export const SOURCES = [
  { name: 'GK2A AMI', url: 'https://zenodo.org/records/20084790', type: 'Historical replay source', provides: 'Thermal hotspot detections used to build the current Punjab and Haryana replay sample.', limit: 'A satellite detection is a candidate observation, not a verified incident. Current UI sample covers Oct–Nov 2025.' },
  { name: 'NASA FIRMS / VIIRS', url: 'https://firms.modaps.eosdis.nasa.gov/active_fire/', type: 'Reference adapter implemented', provides: 'Bounded, date-addressable standard-processing requests normalize source records into BurnBlind observations.', limit: 'Historical FIRMS records are not yet attached to this replay. The API key must be stored in AWS Secrets Manager before acquisition is enabled.' },
  { name: 'Weather / reanalysis', url: 'https://open-meteo.com/en/docs/historical-weather-api', type: 'On-demand investigation context', provides: 'Event-hour ERA5 wind estimates are assembled into the investigation evidence packet with source and timestamp.', limit: 'Reanalysis is not a local measurement. It may be unavailable for a requested event time and cannot establish an active fire.' },
  { name: 'WorldPop', url: 'https://www.worldpop.org/', type: 'On-demand exposure estimate', provides: 'A population sum is requested for a documented directional screening corridor when event-time wind is available.', limit: 'This is a modeled population count, not a smoke-dispersion or health-impact estimate. It is stored with its year, resolution, source and assumptions.' },
];

export function DataPage() {
  return <>
    <PageHeading eyebrow="TRANSPARENCY" title="Data & methodology">Understand what the current replay can show, what it cannot, and how future assessments will be grounded.</PageHeading>
    <section className="source-grid" aria-label="Data sources">{SOURCES.map((source) => <article className="source-card panel" key={source.name}><span className="source-type">{source.type}</span><h2><a href={source.url} target="_blank" rel="noreferrer">{source.name}<span aria-hidden="true"> ↗</span></a></h2><p>{source.provides}</p><div className="source-limit"><strong>LIMITATION</strong><p>{source.limit}</p></div></article>)}</section>
    <section className="method-detail-grid" aria-label="Investigation inputs and outputs">
      <article className="method-detail panel"><p className="eyebrow">INVESTIGATION INPUT</p><h2>One event, one evidence packet</h2><p>The application selects the candidate event and assembles records before Strands runs. The agent is scoped to that event and cannot fetch external data or browse.</p><ul><li>Event identity, location, observation window and attached source IDs</li><li>Timestamped satellite records and deterministic scores, when present</li><li>Event-hour ERA5 context and a WorldPop estimate only when their source calls succeed</li><li>Explicit unavailable or missing-evidence states; missing data is never treated as a negative observation</li></ul></article>
      <article className="method-detail panel"><p className="eyebrow">INVESTIGATION OUTPUT</p><h2>Structured findings for a human</h2><p>The saved JSON report contains a conservative classification, concise summary, evidence findings with packet evidence IDs, contradictions, unavailable evidence and recommendations.</p><ul><li><code>INSUFFICIENT_EVIDENCE</code> when usable event evidence is absent</li><li><code>REVIEW_REQUIRED</code> when meaningful evidence needs a person to assess it</li><li>Only cited packet records may support a claim; corroboration never means a confirmed fire</li><li>Event ID, queue state, timestamps, priority and model metadata are stored by the application beside the report</li></ul></article>
      <article className="method-detail panel"><p className="eyebrow">OPERATIONS</p><h2>How a review starts</h2><p>Scoring rules can queue a review only when an event has the required score inputs. A reviewer can also request one event explicitly; selecting an event does not fan out work to other candidates.</p><ul><li>FIFO queue, one event per message, bounded worker concurrency</li><li>Source evidence and derived context persist separately from the agent report</li><li>Review outcomes are append-only and labeled as human-entered</li><li>Replay controls step through historical event timestamps; the map layers show only persisted sourced records</li></ul></article>
    </section>
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
        {item.investigation?.evidence?.length > 0 && <p className="investigation-card-meta">{item.investigation.evidence.length} cited evidence {item.investigation.evidence.length === 1 ? 'record' : 'records'} · {(item.investigation.recommendations || (item.investigation.recommended_action ? [item.investigation.recommended_action] : [])).map((action) => action.replaceAll('_', ' ')).join(' · ')}</p>}
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
