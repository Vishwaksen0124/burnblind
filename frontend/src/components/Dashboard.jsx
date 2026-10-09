import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, AlertTriangle, Search, Satellite } from 'lucide-react';
import { getActionCenter, getMapLayer, getSummary } from '../api.js';
import { eventLabel, eventSearchText, formatTimestamp } from '../lib/eventView.js';
import { Eyebrow, PageHeading, StateMessage } from './shared.jsx';
import CandidateMap from './CandidateMap.jsx';
import EventDetail from './EventDetail.jsx';

const FILTERS = [
  { id: 'all', label: 'All candidates' },
  { id: 'REQUIRES_REVIEW', label: 'Requires review' },
  { id: 'MORE_EVIDENCE_NEEDED', label: 'More evidence' },
  { id: 'LOW_PRIORITY', label: 'Low priority' },
];

const LAYERS = [
  ['blind-spots', 'Blind spots'],
  ['sensor-disagreement', 'Sensor comparison'],
  ['exposure', 'Potential exposure'],
];

export default function Dashboard() {
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selected, setSelected] = useState(null);
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [buckets, setBuckets] = useState({});
  const [activeLayer, setActiveLayer] = useState('events');
  const [layerResult, setLayerResult] = useState(null);
  const [layerRetry, setLayerRetry] = useState(0);
  const detailRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    Promise.all([getActionCenter(controller.signal, 100), getSummary(controller.signal)])
      .then(([actions, totals]) => {
        setEvents((actions.items || []).map((item) => item.event));
        setBuckets(Object.fromEntries((actions.items || []).map((item) => [item.event.event_id, item.bucket])));
        setSummary(totals);
      })
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    if (activeLayer === 'events') { setLayerResult(null); return undefined; }
    const controller = new AbortController();
    setLayerResult({ status: 'LOADING', items: [] });
    getMapLayer(activeLayer, controller.signal)
      .then(setLayerResult)
      .catch((err) => { if (err.name !== 'AbortError') setLayerResult({ status: 'ERROR', reason: err.message, items: [] }); });
    return () => controller.abort();
  }, [activeLayer, layerRetry]);

  const visibleEvents = useMemo(() => {
    const term = query.trim().toLowerCase();
    return events.filter((event) => {
      const matchesFilter = filter === 'all' || buckets[event.event_id] === filter;
      return matchesFilter && (!term || eventSearchText(event).includes(term));
    });
  }, [events, filter, query, buckets]);

  const dayCounts = useMemo(() => {
    const counts = new Map();
    for (const event of events) {
      const day = event.detected_at_utc?.slice(0, 10);
      if (day) counts.set(day, (counts.get(day) || 0) + 1);
    }
    return [...counts.entries()].sort(([left], [right]) => left.localeCompare(right)).slice(-7);
  }, [events]);

  const sourceCounts = useMemo(() => {
    const counts = new Map();
    for (const event of events) for (const source of event.sources || []) counts.set(source, (counts.get(source) || 0) + 1);
    return [...counts.entries()].sort(([, left], [, right]) => right - left);
  }, [events]);

  const assessmentStats = useMemo(() => {
    const scored = events.filter((event) => event.score_status === 'HEURISTIC_SCORES_AVAILABLE');
    const prioritized = scored.filter((event) => Number.isFinite(event.priority_score) || Number.isFinite(event.provisional_priority_score));
    const review = events.filter((event) => buckets[event.event_id] === 'REQUIRES_REVIEW');
    return { scored: scored.length, prioritized: prioritized.length, review: review.length };
  }, [events, buckets]);

  useEffect(() => {
    if (!selected) return undefined;
    const frame = window.requestAnimationFrame(() => {
      detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [selected?.event_id]);

  function openEvent(event) {
    setSelected(event);
  }

  const activeLayerLabel = LAYERS.find(([id]) => id === activeLayer)?.[1] || 'Candidate events';

  return <>
    <PageHeading eyebrow="ENVIRONMENTAL MONITORING · PUNJAB + HARYANA" title={<>Monitoring <em>overview</em></>} aside={<div className="data-window"><span>LAST OBSERVATION</span><strong>{summary?.last_updated ? formatTimestamp(summary.last_updated) : 'Historical sample'}</strong></div>}>
      Potential thermal observations and coverage gaps across the replay region. Each marker is a candidate detection, not a confirmed incident.
    </PageHeading>

    <section className="ops-strip" aria-label="Replay monitoring summary">
      <div className="ops-stat"><span className="ops-icon"><Activity aria-hidden="true" /></span><span><small>Candidate events</small><strong>{summary ? summary.candidate_events.toLocaleString() : '—'}</strong></span><em>In replay sample</em></div>
      <div className="ops-stat"><span className="ops-icon"><Satellite aria-hidden="true" /></span><span><small>Observation source</small><strong>GK2A AMI</strong></span><em>Oct–Nov 2025</em></div>
      <div className="ops-stat ops-caution"><span className="ops-icon"><AlertTriangle aria-hidden="true" /></span><span><small>Deterministic scoring</small><strong>{assessmentStats.scored}/{events.length || '—'}</strong></span><em>{assessmentStats.prioritized} with priority · {assessmentStats.review} need review</em></div>
      <div className="replay-tag"><i /> HISTORICAL REPLAY</div>
    </section>

    <section className="workspace" aria-label="Monitoring map and candidate event queue">
      <section className="map-panel panel">
        <div className="panel-heading">
          <div><Eyebrow>GEOGRAPHIC DISTRIBUTION</Eyebrow><h2>Punjab + Haryana</h2></div>
          <div className="map-legend"><span className="legend-mark" />{activeLayer === 'events' ? 'Candidate detection' : layerResult?.status === 'AVAILABLE' ? activeLayerLabel : 'Sourced features unavailable'}</div>
        </div>
        <div className="layer-controls" role="group" aria-label="Map data layers">
          <button className={activeLayer === 'events' ? 'layer-button active' : 'layer-button'} onClick={() => setActiveLayer('events')} aria-pressed={activeLayer === 'events'}>Events</button>
          {LAYERS.map(([id, label]) => <button key={id} className={activeLayer === id ? 'layer-button active' : 'layer-button'} onClick={() => setActiveLayer(activeLayer === id ? 'events' : id)} aria-pressed={activeLayer === id}>{label}</button>)}
        </div>
        <div className="map-wrap">
          <CandidateMap events={activeLayer === 'events' || layerResult?.status === 'AVAILABLE' ? visibleEvents : []} onEventSelect={openEvent} layerItems={layerResult?.items || []} activeLayer={activeLayer} />
          <div className="map-overlay"><span>{activeLayer === 'events' ? 'THERMAL OBSERVATIONS · 2025' : activeLayerLabel.toUpperCase()}</span><strong>{activeLayer === 'events' ? visibleEvents.length : layerResult?.status === 'AVAILABLE' ? layerResult.items.length : '—'}</strong><small>{activeLayer === 'events' ? 'visible candidates' : layerResult?.status === 'AVAILABLE' ? 'sourced records' : layerResult?.status === 'LOADING' ? 'Loading sourced layer…' : 'Unavailable for this replay'}</small></div>
          <div className="map-coordinates" aria-hidden="true">29°N — 33°N<br />74°E — 78°E</div>
        </div>
        {layerResult && layerResult.status !== 'AVAILABLE' && <div className="layer-empty-state" role="status"><div><strong>{layerResult.status === 'LOADING' ? `Loading ${activeLayerLabel.toLowerCase()}…` : `No ${activeLayerLabel.toLowerCase()} data for this replay`}</strong><p>{layerResult.reason || (layerResult.status === 'LOADING' ? 'Requesting sourced feature records.' : 'No sourced records were returned. An empty layer does not mean the feature is absent.')}</p></div><div className="layer-empty-actions">{layerResult.status === 'ERROR' && <button className="text-button" onClick={() => setLayerRetry((value) => value + 1)}>Retry</button>}<button className="text-button" onClick={() => setActiveLayer('events')}>Show candidate events</button></div></div>}
        <div className="map-foot"><span>{activeLayer === 'events' ? 'GK2A HISTORICAL DETECTIONS' : `${activeLayerLabel.toUpperCase()} · SOURCED RECORDS ONLY`}</span><span>COORDINATE REFERENCE · WGS84</span></div>
      </section>

      <aside className="queue-panel panel" aria-label="Candidate event queue">
        <div className="panel-heading queue-title">
          <div><Eyebrow>ACTION CENTER · DETERMINISTIC TRIAGE</Eyebrow><h2>Candidate events <span className="count-pill">{loading ? '…' : visibleEvents.length}</span></h2><p className="queue-scope">Showing {loading ? 'events' : `${visibleEvents.length} of ${events.length} loaded`} · {summary?.candidate_events ?? '—'} total candidates</p></div>
        </div>
        <label className="search-box"><Search aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search source or event" aria-label="Search candidate events" /></label>
        <div className="filter-list" role="group" aria-label="Filter candidate events">
          {FILTERS.map((item) => <button key={item.id} className={filter === item.id ? 'filter-button active' : 'filter-button'} onClick={() => setFilter(item.id)} aria-pressed={filter === item.id}>{item.label}</button>)}
        </div>
        {loading && <div className="loading-list" aria-label="Loading replay events"><i /><i /><i /></div>}
        {error && !loading && <StateMessage title="Event data unavailable">We could not load the replay data. <button className="text-button" onClick={() => setRetry((value) => value + 1)}>Retry</button></StateMessage>}
        {!loading && !error && visibleEvents.length === 0 && <StateMessage title="No candidate events">No replay observations match this view.</StateMessage>}
        {!loading && !error && visibleEvents.length > 0 && <div className="event-list">
          {visibleEvents.map((event) => <button className={`event-row ${selected?.event_id === event.event_id ? 'selected' : ''}`} key={event.event_id} onClick={() => openEvent(event)}>
            <span className="candidate-mark" aria-hidden="true" />
            <span className="event-copy"><strong>{eventLabel(event)}</strong><small>{formatTimestamp(event.detected_at_utc)} · {event.sources.join(' + ')}</small><span className="event-meta"><b className={`action-bucket bucket-${buckets[event.event_id]?.toLowerCase()}`}>{(buckets[event.event_id] || 'MORE_EVIDENCE_NEEDED').replaceAll('_', ' ')}</b> · {event.detection_count} {event.detection_count === 1 ? 'detection' : 'detections'} · <b className="event-priority">{Number.isFinite(event.priority_score) ? `Priority ${event.priority_score.toFixed(2)}` : Number.isFinite(event.provisional_priority_score) ? `Provisional priority ${event.provisional_priority_score.toFixed(2)}` : 'Priority pending'}</b></span></span>
          </button>)}
        </div>}
        <p className="queue-note">Triage uses attached deterministic scores. Unscored candidates stay in “More evidence needed”; missing inputs never count as negative evidence.</p>
      </aside>
    </section>

    <section className="monitoring-context" aria-label="Replay data context">
      <article className="context-panel panel">
        <header><div><Eyebrow>OBSERVATION RHYTHM</Eyebrow><h2>Events by UTC day</h2></div><span>LOADED CANDIDATES</span></header>
        {dayCounts.length > 0 ? <div className="activity-chart" role="img" aria-label={dayCounts.map(([day, count]) => day + ': ' + count + ' events').join('; ')}>
          {dayCounts.map(([day, count]) => <div className="activity-column" key={day}><strong>{count}</strong><i style={{ height: Math.max(8, (count / Math.max(...dayCounts.map(([, value]) => value))) * 72) + 'px' }} /><span>{new Date(day + 'T00:00:00Z').toLocaleDateString('en-GB', { day: '2-digit', month: 'short', timeZone: 'UTC' })}</span></div>)}
        </div> : <p className="context-empty">Daily distribution appears when observations are available.</p>}
        <p className="context-foot">Counts describe the events currently loaded in this view, not a live incident rate.</p>
      </article>
      <article className="context-panel panel">
        <header><div><Eyebrow>SOURCE COVERAGE</Eyebrow><h2>Records by source</h2></div><span>OBSERVATION LINKS</span></header>
        {sourceCounts.length > 0 ? <ul className="source-bars">{sourceCounts.map(([source, count]) => <li key={source}><span>{source}</span><i><b style={{ width: (count / Math.max(...sourceCounts.map(([, value]) => value))) * 100 + '%' }} /></i><strong>{count}</strong></li>)}</ul> : <p className="context-empty">Source counts are unavailable until event records load.</p>}
        <p className="context-foot">Multiple linked records can belong to one candidate. A source count does not indicate independent confirmation.</p>
      </article>
    </section>

    {selected && <div ref={detailRef} className="monitoring-selection"><EventDetail event={selected} onClose={() => setSelected(null)} /></div>}
  </>;
}
