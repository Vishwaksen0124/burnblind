import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { getEvents } from '../api.js';
import { formatTimestamp } from '../lib/eventView.js';
import { Eyebrow, PageHeading, StateMessage } from './shared.jsx';
import CandidateMap from './CandidateMap.jsx';
import EventDetail from './EventDetail.jsx';

export default function ReplayPage() {
  const [events, setEvents] = useState([]);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    async function loadAll() {
      setLoading(true);
      try {
        const collected = [];
        let cursor;
        for (let pageNumber = 0; pageNumber < 50; pageNumber += 1) {
          const page = await getEvents(controller.signal, 100, cursor);
          collected.push(...(page.items || []));
          cursor = page.next_cursor;
          if (!cursor) break;
        }
        collected.sort((left, right) => left.detected_at_utc.localeCompare(right.detected_at_utc));
        setEvents(collected);
        setIndex(Math.max(0, collected.length - 1));
        setError('');
      } catch (cause) {
        if (cause.name !== 'AbortError') setError(cause.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    loadAll();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!playing || events.length < 2) return undefined;
    const timer = window.setInterval(() => {
      if (index >= events.length - 1) setPlaying(false);
      else setIndex((current) => current + 1);
    }, 1000 / speed);
    return () => window.clearInterval(timer);
  }, [playing, speed, events.length, index]);

  const visibleEvents = useMemo(() => events.slice(0, index + 1), [events, index]);
  const current = events[index];

  return <>
    <PageHeading eyebrow="HISTORICAL REPLAY · PUNJAB + HARYANA" title={<>Replay the <em>evidence</em></>} aside={<div className="data-window"><span>REPLAY POSITION</span><strong>{current ? formatTimestamp(current.detected_at_utc) : '—'}</strong></div>}>
      Step through the recorded candidate observations in timestamp order. This is a historical dataset replay, not a live feed or a simulation of fire spread.
    </PageHeading>
    {loading && <StateMessage title="Loading replay timeline">Reading the historical event pages.</StateMessage>}
    {error && !loading && <StateMessage title="Replay data unavailable">{error}</StateMessage>}
    {!loading && !error && events.length === 0 && <StateMessage title="No replay events">No historical observations are available.</StateMessage>}
    {!loading && !error && events.length > 0 && <>
      <section className="replay-controls panel" aria-label="Historical replay controls">
        <div className="replay-buttons">
          <button className="replay-step" onClick={() => { setPlaying(false); setIndex((value) => Math.max(0, value - 1)); }} disabled={index === 0} aria-label="Previous observation"><ChevronLeft aria-hidden="true" /></button>
          <button className="action-button replay-toggle" onClick={() => { if (index === events.length - 1) setIndex(0); setPlaying((value) => !value); }} aria-label={playing ? 'Pause replay' : 'Play replay'}>{playing ? 'Pause' : 'Play'}</button>
          <button className="replay-step" onClick={() => { setPlaying(false); setIndex((value) => Math.min(events.length - 1, value + 1)); }} disabled={index === events.length - 1} aria-label="Next observation"><ChevronRight aria-hidden="true" /></button>
          <label className="replay-speed">Speed<select value={speed} onChange={(event) => setSpeed(Number(event.target.value))}><option value="0.5">0.5×</option><option value="1">1×</option><option value="2">2×</option><option value="4">4×</option></select></label>
        </div>
        <label className="replay-range"><span>{events[0] ? formatTimestamp(events[0].detected_at_utc) : ''}</span><input type="range" min="0" max={events.length - 1} value={index} onChange={(event) => { setPlaying(false); setIndex(Number(event.target.value)); }} aria-label="Replay timestamp" /><span>{events.at(-1) ? formatTimestamp(events.at(-1).detected_at_utc) : ''}</span></label>
        <p className="replay-counter"><strong>{visibleEvents.length.toLocaleString()}</strong> of {events.length.toLocaleString()} candidate observations shown · events do not imply confirmed incidents</p>
      </section>
      <section className="replay-map panel"><div className="panel-heading"><div><Eyebrow>OBSERVATIONS UP TO REPLAY TIME</Eyebrow><h2>{current ? formatTimestamp(current.detected_at_utc) : 'No timestamp selected'}</h2></div><span className="replay-tag">HISTORICAL REPLAY</span></div><div className="map-wrap"><CandidateMap events={visibleEvents} onEventSelect={setSelected} /></div></section>
      {selected && <EventDetail event={selected} onClose={() => setSelected(null)} />}
    </>}
  </>;
}
