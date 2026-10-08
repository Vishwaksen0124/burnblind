import { useEffect, useMemo, useState } from 'react';
import { CircleMarker, MapContainer, TileLayer, Tooltip, ZoomControl } from 'react-leaflet';
import { getEvents, getSummary } from '../api.js';
import { eventLabel, eventSearchText, formatTimestamp } from '../lib/eventView.js';
import { Eyebrow, PageHeading, StateMessage } from './shared.jsx';
import EventDetail from './EventDetail.jsx';

const REGION_BOUNDS = [[28.75, 73.75], [32.75, 77.85]];
const FILTERS = [
  { id: 'all', label: 'All candidates' },
  { id: 'repeated', label: 'Repeated detections' },
  { id: 'single', label: 'Single detections' },
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

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    Promise.all([getEvents(controller.signal, 100), getSummary(controller.signal)])
      .then(([page, totals]) => { setEvents(page.items); setSummary(totals); })
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [retry]);

  const visibleEvents = useMemo(() => {
    const term = query.trim().toLowerCase();
    return events.filter((event) => {
      const matchesFilter = filter === 'all' || (filter === 'repeated' ? event.detection_count > 1 : event.detection_count === 1);
      return matchesFilter && (!term || eventSearchText(event).includes(term));
    });
  }, [events, filter, query]);

  function openEvent(event) {
    setSelected(event);
  }

  return <>
    <PageHeading eyebrow="ENVIRONMENTAL MONITORING · PUNJAB + HARYANA" title={<>Monitoring <em>overview</em></>} aside={<div className="data-window"><span>DATA WINDOW</span><strong>{summary?.last_updated ? formatTimestamp(summary.last_updated) : 'Historical sample'}</strong></div>}>
      Explore grouped satellite detections and monitoring coverage gaps across the replay region. Every item is a candidate observation, not a confirmed fire.
    </PageHeading>

    <div className="replay-strip"><span className="replay-icon">↺</span><strong>HISTORICAL REPLAY</strong><span>GK2A · Oct–Nov 2025 source sample</span><span className="strip-separator" />{summary && <span>{summary.candidate_events.toLocaleString()} candidate clusters in dataset</span>}</div>

    <section className="workspace" aria-label="Monitoring map and candidate event queue">
      <section className="map-panel panel">
        <div className="panel-heading">
          <div><Eyebrow>GEOGRAPHIC DISTRIBUTION</Eyebrow><h2>Punjab + Haryana</h2></div>
          <div className="map-legend"><span className="legend-mark" />Candidate detection</div>
        </div>
        <div className="map-wrap">
          <MapContainer bounds={REGION_BOUNDS} boundsOptions={{ padding: [18, 18] }} minZoom={6} maxZoom={12} scrollWheelZoom className="map" zoomControl={false}>
            <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <ZoomControl position="bottomright" />
            {visibleEvents.map((event) => <CircleMarker key={event.event_id} center={[event.latitude, event.longitude]} radius={event.detection_count > 1 ? 7 : 5} pathOptions={{ color: '#ffc16b', weight: 1.5, fillColor: '#e9753b', fillOpacity: 0.78 }} eventHandlers={{ click: () => openEvent(event) }}>
              <Tooltip><strong>{eventLabel(event)}</strong><br />{formatTimestamp(event.detected_at_utc)}</Tooltip>
            </CircleMarker>)}
          </MapContainer>
          <div className="map-overlay"><span>REPLAY · 2025</span><strong>{visibleEvents.length}</strong><small>candidate observations</small></div>
          <div className="map-coordinates" aria-hidden="true">29°N — 33°N<br />74°E — 78°E</div>
        </div>
        <div className="map-foot"><span>GK2A HISTORICAL DETECTIONS</span><span>COORDINATE REFERENCE · WGS84</span></div>
      </section>

      <aside className="queue-panel panel" aria-label="Candidate event queue">
        <div className="panel-heading queue-title">
          <div><Eyebrow>REPLAY EVENT QUEUE</Eyebrow><h2>Potential events <span className="count-pill">{loading ? '…' : visibleEvents.length}</span></h2></div>
        </div>
        <label className="search-box"><span aria-hidden="true">⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search source or event" aria-label="Search candidate events" /></label>
        <div className="filter-list" role="group" aria-label="Filter candidate events">
          {FILTERS.map((item) => <button key={item.id} className={filter === item.id ? 'filter-button active' : 'filter-button'} onClick={() => setFilter(item.id)} aria-pressed={filter === item.id}>{item.label}</button>)}
        </div>
        {loading && <div className="loading-list" aria-label="Loading replay events"><i /><i /><i /></div>}
        {error && !loading && <StateMessage title="Event data unavailable">We could not load the replay data. <button className="text-button" onClick={() => setRetry((value) => value + 1)}>Retry</button></StateMessage>}
        {!loading && !error && visibleEvents.length === 0 && <StateMessage title="No candidate events">No replay observations match this view.</StateMessage>}
        {!loading && !error && visibleEvents.length > 0 && <div className="event-list">
          {visibleEvents.map((event) => <button className={`event-row ${selected?.event_id === event.event_id ? 'selected' : ''}`} key={event.event_id} onClick={() => openEvent(event)}>
            <span className="candidate-mark" aria-hidden="true" />
            <span className="event-copy"><strong>{eventLabel(event)}</strong><small>{formatTimestamp(event.detected_at_utc)} · {event.sources.join(' + ')}</small><span className="event-meta">{event.detection_count} {event.detection_count === 1 ? 'detection' : 'detections'} <i>·</i> {event.latitude.toFixed(2)}°, {event.longitude.toFixed(2)}°</span></span>
          </button>)}
        </div>}
        <p className="queue-note">Priorities and investigation status are unavailable for this historical sample.</p>
      </aside>
    </section>

    {selected && <EventDetail event={selected} onClose={() => setSelected(null)} />}
  </>;
}
