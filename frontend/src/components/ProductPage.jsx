import { useEffect, useState } from 'react';
import { getEvents, getSummary } from '../api.js';
import { eventLabel, formatTimestamp } from '../lib/eventView.js';
import CandidateMap from './CandidateMap.jsx';
import { SOURCES } from './SupportingPages.jsx';

const STORY_STEPS = [
  ['01', 'Observe', 'Group thermal observations by place and time, keeping the source and observation window attached.'],
  ['02', 'See the gaps', 'Make incomplete coverage and uncertainty visible instead of treating missing observations as proof.'],
  ['03', 'Review the evidence', 'Bring source context together so a person can decide what deserves a closer look.'],
];

export default function ProductPage() {
  const [events, setEvents] = useState([]);
  const [eventTotal, setEventTotal] = useState(null);
  const [previewError, setPreviewError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([getEvents(controller.signal, 8), getSummary(controller.signal)])
      .then(([page, summary]) => {
        setEvents(page.items);
        setEventTotal(summary.candidate_events);
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setPreviewError(true);
      });
    return () => controller.abort();
  }, []);

  return <div className="product-page">
    <section className="product-hero" id="home" aria-labelledby="product-title">
      <div className="hero-copy">
        <p className="product-kicker"><span /> ENVIRONMENTAL INTELLIGENCE · PUNJAB + HARYANA</p>
        <h1 id="product-title">Seeing the fires<br />others <em>might miss.</em></h1>
        <p className="hero-description">BurnBlind brings satellite observations and monitoring gaps into one place, so potential fire events can be examined with their evidence and uncertainty in view.</p>
        <div className="hero-actions"><a className="primary-button" href="#monitoring">Explore monitoring <span aria-hidden="true">→</span></a><a className="secondary-button" href="#landing-how-it-works">How it works</a></div>
        <p className="hero-caveat">Historical replay · Oct–Nov 2025 · Candidate observations, not confirmed incidents</p>
      </div>
      <div className="hero-visual">
        <img className="hero-background-image" src="/images/nasa-punjab-smoke-2024.jpg" alt="Satellite view of smoke over Punjab and Haryana on November 8, 2024" fetchPriority="high" />
        <div className="hero-image-shade" aria-hidden="true" />
        <div className="hero-image-meta"><span>SATELLITE CONTEXT · 08 NOV 2024</span><a href="https://science.nasa.gov/earth/earth-observatory/is-fire-activity-declining-in-northwestern-india-153826/" target="_blank" rel="noreferrer">NASA Earth Observatory ↗</a><small>VIIRS / Suomi NPP · Image by Wanmei Liang</small></div>
        <div className="hero-coordinates">PUNJAB + HARYANA<br />NORTHWESTERN INDIA</div>
      </div>
      <a className="scroll-cue" href="#why-burnblind"><span /> Read the observation gap</a>
    </section>

    <section className="story-section problem-section" id="why-burnblind">
      <div className="section-index">01 / THE PROBLEM</div>
      <div className="problem-copy"><h2>No single observation<br />shows the whole picture.</h2><p>Satellite passes are snapshots. Clouds, timing, sensor coverage, and incomplete context can leave uncertainty around what was observed—and what was not.</p><p>BurnBlind keeps those limits visible while helping people find candidate events worth a closer look.</p></div>
      <div className="problem-mark" aria-hidden="true"><span className="contour contour-one" /><span className="contour contour-two" /><span className="contour contour-three" /><i /></div>
    </section>

    <section className="story-section method-section" id="landing-how-it-works">
      <div className="section-heading"><div><div className="section-index">02 / HOW BURNBLIND SEES</div><h2>From observation to<br /><em>evidence-led review.</em></h2></div><p>Each step keeps the source and its limitations attached. A detection is a starting point, not a verdict.</p></div>
      <div className="story-steps">{STORY_STEPS.map(([number, title, description]) => <article className="story-step" key={number}><span>{number}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
    </section>

    <section className="preview-section" aria-labelledby="preview-title">
      <div className="section-heading preview-heading"><div><div className="section-index">03 / THE PRODUCT</div><h2 id="preview-title">A clearer view of<br /><em>the replay region.</em></h2></div><a className="text-link" href="#monitoring">Open monitoring <span aria-hidden="true">↗</span></a></div>
      <div className="product-preview">
        <div className="preview-toolbar"><span className="preview-brand"><i /> BURNBLIND</span><span>MONITORING / PUNJAB + HARYANA</span><span className="preview-replay">HISTORICAL REPLAY · 2025</span></div>
        <div className="preview-stats"><div><small>CANDIDATE EVENTS</small><strong>{eventTotal === null ? '—' : eventTotal.toLocaleString()}</strong></div><div><small>OBSERVATION SOURCE</small><strong>GK2A AMI</strong></div><div><small>ASSESSMENT</small><strong className="preview-unavailable">Not scored</strong></div></div>
        <div className="preview-workspace"><div className="preview-map"><CandidateMap events={events} className="map preview-map-canvas" interactive={false} zoomControl={false} /><span className="preview-map-note">Candidate observations · WGS84</span></div>
          <div className="preview-queue"><div className="preview-queue-title"><span>REPLAY EVENT QUEUE</span><strong>{events.length ? events.length : '—'}</strong></div>
            {events.slice(0, 5).map((event) => <div className="preview-event" key={event.event_id}><i /><span><strong>{eventLabel(event)}</strong><small>{event.sources.join(' + ') || 'Source metadata unavailable'} · {formatTimestamp(event.detected_at_utc)}</small></span></div>)}
            {previewError && <p className="preview-empty">Replay data is temporarily unavailable.</p>}
            {!previewError && events.length === 0 && <p className="preview-empty">Loading historical observations…</p>}
          </div>
        </div>
      </div>
      <p className="preview-caption">A live view of the replay dataset—not a live incident feed. Selecting a candidate opens its source details and investigation status.</p>
    </section>

    <section className="story-section impact-section">
      <div className="section-index">04 / WHY IT MATTERS</div>
      <div className="impact-copy"><h2>Make uncertainty<br /><em>visible and useful.</em></h2><p>Environmental monitoring works best when observations are traceable, limitations are explicit, and decisions stay with the people responsible for them.</p><a className="text-link" href="#methodology">Explore data & methodology <span aria-hidden="true">→</span></a></div>
      <div className="impact-principles"><p><span>OBSERVED</span>Keep the original source and time context close to every candidate.</p><p><span>UNCERTAIN</span>Show what the replay cannot establish.</p><p><span>HUMAN-LED</span>Use investigation reports as advisory evidence for review.</p></div>
    </section>

    <section className="sources-section" id="methodology">
      <div className="section-heading" id="landing-methodology"><div><div className="section-index">05 / DATA & LIMITATIONS</div><h2>Know what the data<br /><em>can—and cannot—say.</em></h2></div><p>Source transparency is part of the interface. Event-level availability reflects stored evidence and active integrations.</p></div>
      <div className="landing-source-grid">{SOURCES.map((source) => <article className="landing-source" key={source.name}><span>{source.type}</span><h3><a href={source.url} target="_blank" rel="noreferrer">{source.name} ↗</a></h3><p>{source.provides}</p><small>{source.limit}</small></article>)}</div>
      <div className="limitations-row"><strong>Current replay boundaries</strong><span>Historical sample · Oct–Nov 2025</span><span>No seeded score inputs · exposure is per event</span><span>No independent fire confirmation</span></div>
    </section>

    <section className="agent-section">
      <div className="agent-index">06 / INVESTIGATION AGENT</div><div><h2>Evidence organized<br />for human review.</h2><p>Strands assembles source-backed findings, contradictions, missing evidence, and a human-review recommendation from one event-scoped packet. Bedrock Mantle with DeepSeek V3.2 completed a live event-scoped smoke investigation on 09 Oct 2026; the report remains advisory and makes no operational decisions.</p><p className="agent-status"><i /> Live model path verified · one event · 25 seconds</p></div><a className="secondary-button" href="#investigations">Investigation details <span aria-hidden="true">→</span></a>
    </section>

    <section className="final-cta"><div className="section-index">07 / EXPLORE THE REPLAY</div><h2>Start with what<br />the satellites <em>observed.</em></h2><p>Explore grouped thermal observations across Punjab and Haryana, with source context and uncertainty kept in view.</p><a className="primary-button" href="#monitoring">Open monitoring <span aria-hidden="true">→</span></a></section>
  </div>;
}
