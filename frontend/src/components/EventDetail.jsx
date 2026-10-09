import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, Clock3, FileCode2, MapPin, Satellite, UsersRound, X } from 'lucide-react';
import { getEnvironmentalAnalysis, getExposure, getInvestigation, getReviewOutcomes, getSensorComparison, requestEnvironmentalAnalysis, requestInvestigation, submitReviewOutcome } from '../api.js';
import { formatCoordinate, formatTimestamp } from '../lib/eventView.js';
import { useReviewerAuth } from '../reviewerAuth.jsx';

const ACTIVE_STATUSES = new Set(['QUEUED', 'RUNNING']);

export default function EventDetail({ event, onClose, initialTab = 'event' }) {
  const reviewerAuth = useReviewerAuth();
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('event');
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [reviewOutcome, setReviewOutcome] = useState('NEEDS_VERIFICATION');
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewBusy, setReviewBusy] = useState(false);
  const [addingAnotherReview, setAddingAnotherReview] = useState(false);
  const [reviewError, setReviewError] = useState('');
  const [sensorComparison, setSensorComparison] = useState(null);
  const [exposure, setExposure] = useState(null);
  const [environmental, setEnvironmental] = useState(null);
  const [environmentalBusy, setEnvironmentalBusy] = useState(false);
  const [environmentalError, setEnvironmentalError] = useState('');

  const refresh = useCallback(async (signal) => {
    const value = await getInvestigation(event.event_id, signal);
    setRecord(value);
    return value;
  }, [event.event_id]);

  useEffect(() => {
    const controller = new AbortController();
    let investigationTimer;
    const poll = async () => {
      try {
        const value = await refresh(controller.signal);
        setError('');
        if (ACTIVE_STATUSES.has(value.status)) investigationTimer = window.setTimeout(poll, 2500);
      } catch (err) {
        if (err.name !== 'AbortError') setError(err.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    setLoading(true);
    setRecord(null);
    setReviews([]);
    setReviewsLoading(true);
    setReviewError('');
    setSensorComparison(null);
    setExposure(null);
    setEnvironmental(null);
    setEnvironmentalError('');
    setActiveTab(initialTab);
    poll();
    getReviewOutcomes(event.event_id, controller.signal)
      .then((value) => setReviews(value.items || []))
      .catch((err) => { if (err.name !== 'AbortError') setReviewError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setReviewsLoading(false); });
    getSensorComparison(event.event_id, controller.signal)
      .then(setSensorComparison)
      .catch((err) => { if (err.name !== 'AbortError') setSensorComparison({ status: 'ERROR', reason: err.message }); });
    getExposure(event.event_id, controller.signal)
      .then(setExposure)
      .catch((err) => { if (err.name !== 'AbortError') setExposure({ status: 'ERROR', reason: err.message }); });
    getEnvironmentalAnalysis(event.event_id, controller.signal)
      .then(setEnvironmental)
      .catch((err) => { if (err.name !== 'AbortError') setEnvironmentalError(err.message); });
    return () => { controller.abort(); window.clearTimeout(investigationTimer); };
  }, [refresh, initialTab]);

  useEffect(() => {
    if (environmental?.status !== 'PROCESSING') return undefined;
    const controller = new AbortController();
    let timer;
    const poll = async () => {
      try {
        const current = await getEnvironmentalAnalysis(event.event_id, controller.signal);
        setEnvironmental(current);
        if (current.status === 'PROCESSING') timer = window.setTimeout(poll, 2500);
        else if (current.status === 'COMPLETE' || current.status === 'PARTIAL') {
          const [comparison, population] = await Promise.all([
            getSensorComparison(event.event_id, controller.signal),
            getExposure(event.event_id, controller.signal),
          ]);
          setSensorComparison(comparison);
          setExposure(population);
        }
      } catch (err) {
        if (err.name !== 'AbortError') setEnvironmentalError(err.message);
      }
    };
    timer = window.setTimeout(poll, 1500);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [event.event_id, environmental?.status]);

  async function startEnvironmentalAnalysis() {
    if (!reviewerAuth.session) {
      reviewerAuth.openSignIn('Sign in with an invited reviewer account to request sourced environmental analysis.');
      return;
    }
    setEnvironmentalBusy(true);
    setEnvironmentalError('');
    try {
      const value = await requestEnvironmentalAnalysis(event.event_id, reviewerAuth.session.token);
      setEnvironmental(value);
    } catch (err) {
      setEnvironmentalError(err.message);
    } finally {
      setEnvironmentalBusy(false);
    }
  }

  async function startInvestigation() {
    if (!reviewerAuth.session) {
      reviewerAuth.openSignIn('Sign in with an invited reviewer account to request an investigation for this event.');
      return;
    }
    setRequesting(true);
    setError('');
    try {
      const result = await requestInvestigation(event.event_id, reviewerAuth.session.token);
      setRecord((current) => ({ ...current, status: result.status }));
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setRequesting(false);
    }
  }

  async function saveReview(eventValue) {
    eventValue.preventDefault();
    if (!reviewerAuth.session) {
      reviewerAuth.openSignIn('Sign in with an invited reviewer account to record a human review outcome.');
      return;
    }
    setReviewBusy(true);
    setReviewError('');
    try {
      const value = await submitReviewOutcome(event.event_id, reviewOutcome, reviewNotes, reviewerAuth.session.token);
      setReviews((current) => [value.review, ...current]);
      setReviewNotes('');
      setAddingAnotherReview(false);
    } catch (err) {
      setReviewError(err.message);
    } finally {
      setReviewBusy(false);
    }
  }

  function handleTabKeyDown(event) {
    const tabs = ['event', 'investigation'];
    const currentIndex = tabs.indexOf(activeTab);
    let nextIndex = currentIndex;
    if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % tabs.length;
    else if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    else if (event.key === 'Home') nextIndex = 0;
    else if (event.key === 'End') nextIndex = tabs.length - 1;
    else return;
    event.preventDefault();
    setActiveTab(tabs[nextIndex]);
    document.getElementById(`${tabs[nextIndex]}-tab`)?.focus();
  }

  const report = record?.investigation;
  const hasScores = event.score_status === 'HEURISTIC_SCORES_AVAILABLE';
  const comparisonAvailable = sensorComparison?.status === 'AVAILABLE';
  const exposureAvailable = exposure?.status === 'AVAILABLE';
  return <section className="detail-section panel" aria-labelledby="event-detail-title">
    <div className="detail-heading candidate-heading"><div className="candidate-heading-main"><p className="eyebrow">OBSERVATION SUMMARY</p><h2 id="event-detail-title">{event.detection_count > 1 ? 'Grouped candidate event' : 'Candidate event'}</h2><p className="candidate-location"><MapPin aria-hidden="true" />{formatCoordinate(event.latitude, 'N')} <span>·</span> {formatCoordinate(event.longitude, 'E')}</p></div><div className="candidate-heading-actions"><span className="candidate-state"><i aria-hidden="true" />Unverified observation</span><button className="close-button" onClick={onClose} aria-label="Close event details"><X aria-hidden="true" /></button></div></div>
    <div className="detail-tabs" role="tablist" aria-label="Event review sections" onKeyDown={handleTabKeyDown}>
      <button id="event-tab" role="tab" aria-selected={activeTab === 'event'} aria-controls="event-panel" tabIndex={activeTab === 'event' ? 0 : -1} onClick={() => setActiveTab('event')}>Event details</button>
      <button id="investigation-tab" role="tab" aria-selected={activeTab === 'investigation'} aria-controls="investigation-panel" tabIndex={activeTab === 'investigation' ? 0 : -1} onClick={() => setActiveTab('investigation')}>
        Investigation report{record?.status === 'FAILED' && <span className="tab-state tab-state-failed">Failed</span>}{record?.status === 'COMPLETED' && <span className="tab-state tab-state-complete">Ready</span>}
      </button>
    </div>
    <div id="event-panel" className="detail-tab-panel" role="tabpanel" aria-labelledby="event-tab" hidden={activeTab !== 'event'}>
      <div className="candidate-facts">
        <div className="candidate-fact"><span className="fact-icon"><Clock3 aria-hidden="true" /></span><div><span className="detail-label">OBSERVED</span><strong>{formatTimestamp(event.detected_at_utc)}</strong><small>{event.last_observed_at_utc && event.last_observed_at_utc !== event.detected_at_utc ? `Last seen ${formatTimestamp(event.last_observed_at_utc)}` : 'Single recorded observation'}</small></div></div>
        <div className="candidate-fact"><span className="fact-icon"><Satellite aria-hidden="true" /></span><div><span className="detail-label">SOURCE RECORD</span><strong>{(event.sources || []).map(formatSource).join(' · ') || 'Source unavailable'}</strong><small>{event.detection_count} {event.detection_count === 1 ? 'linked detection' : 'linked detections'}</small></div></div>
        <div className={`candidate-fact candidate-assessment${hasScores ? '' : ' is-unavailable'}`}><span className="fact-icon"><FileCode2 aria-hidden="true" /></span><div><span className="detail-label">DETERMINISTIC ASSESSMENT</span><strong>{hasScores ? 'Scores available' : 'Awaiting feature data'}</strong><small>{hasScores ? `Fire signal ${formatScore(event.fire_likelihood)} · uncertainty ${formatScore(event.uncertainty)} · priority ${formatScore(event.priority_score)}` : 'Required scoring inputs are not attached to this candidate.'}</small></div></div>
      </div>
      <div className="evidence-context-heading"><div><p className="eyebrow">SUPPORTING CONTEXT</p><h3>What else is known</h3></div><button className="context-action" type="button" onClick={() => setActiveTab('investigation')}>Open investigation <ArrowRight aria-hidden="true" /></button></div>
      <div className="environmental-analysis-action">
        <div><span className="detail-label">SOURCE BASED ENVIRONMENTAL ANALYSIS</span><p>{environmental?.status === 'PROCESSING' ? 'Weather and population sources are being queried. This does not run the investigation agent.' : environmental?.result?.environmental_analysis?.updated_at_utc ? `Last updated ${formatTimestamp(environmental.result.environmental_analysis.updated_at_utc)} · deterministic source analysis` : 'Estimate event-time weather and potential population exposure from cited sources.'}</p></div>
        <button className="action-button" type="button" disabled={environmentalBusy || environmental?.status === 'PROCESSING' || environmental?.status === 'COMPLETE'} onClick={startEnvironmentalAnalysis}>{environmentalBusy || environmental?.status === 'PROCESSING' ? 'Analyzing…' : environmental?.status === 'COMPLETE' ? 'Analysis complete' : environmental?.status === 'PARTIAL' ? 'Retry analysis' : 'Run environmental analysis'}</button>
      </div>
      {environmentalError && <p className="report-error" role="alert">Environmental analysis unavailable: {environmentalError}</p>}
      <div className="event-feature-grid">
        <ContextCard icon={<Satellite aria-hidden="true" />} title="Cross-sensor comparison" state={sensorComparison?.status} value={comparisonAvailable ? sensorComparison.result?.status?.replaceAll('_', ' ') || 'Comparison available' : null} detail={comparisonAvailable ? sensorComparison.result?.reason || 'A matched second-sensor record is attached.' : sensorComparison?.status === 'ERROR' ? sensorComparison.reason : 'No matched observation from a second sensor is attached to this candidate.'} evidenceIds={comparisonAvailable ? sensorComparison.result?.evidence_ids : null} />
        <ContextCard icon={<UsersRound aria-hidden="true" />} title="Potential population exposure" state={exposure?.status} value={exposureAvailable && Number.isFinite(exposure.result?.population_estimate) ? `${Math.round(exposure.result.population_estimate).toLocaleString()} people (estimated)` : null} detail={exposureAvailable ? `${exposure.result?.source || 'Sourced estimate'}${exposure.result?.method ? ` · ${exposure.result.method.replaceAll('_', ' ')}` : ''}` : exposure?.status === 'ERROR' ? exposure.reason : 'Run environmental analysis to estimate using event-time reanalysis and WorldPop.'} />
        <ContextCard icon={<Clock3 aria-hidden="true" />} title="Event-time weather" state={environmental?.result?.environmental_analysis?.weather?.status} value={environmental?.result?.environmental_analysis?.weather?.status === 'OK' ? `${environmental.result.environmental_analysis.weather.wind_speed_m_s.toFixed(1)} m/s · ${Math.round(environmental.result.environmental_analysis.weather.wind_direction_degrees)}°` : null} detail={environmental?.result?.environmental_analysis?.weather?.status === 'OK' ? `${environmental.result.environmental_analysis.weather.source} · reanalysis estimate` : 'Available after running source based environmental analysis.'} evidenceIds={environmental?.result?.environmental_analysis?.weather?.evidence_id ? [environmental.result.environmental_analysis.weather.evidence_id] : null} />
        <ContextCard icon={<Satellite aria-hidden="true" />} title="Monitoring blind spot" state={environmental?.result?.blind_spot?.status} value={environmental?.result?.blind_spot?.score != null ? `${environmental.result.blind_spot.score} score` : null} detail={environmental?.result?.blind_spot?.detail || 'Requires sourced acquisition coverage and quality records; a detection gap alone is not enough.'} />
      </div>
      <div className="candidate-integrity-note"><span>Evidence boundary</span><p>This record describes a satellite observation. It does not verify an active fire.</p></div>
      <details className="candidate-reference"><summary>Technical record reference</summary><code>{event.event_id}</code><span>Historical replay · Punjab and Haryana</span></details>
    </div>
    <div id="investigation-panel" className="detail-tab-panel" role="tabpanel" aria-labelledby="investigation-tab" hidden={activeTab !== 'investigation'}>
    <div className="investigation-report" aria-live="polite">
      <div className="investigation-report-heading"><div><p className="eyebrow">EVIDENCE REVIEW</p><h3>Investigation</h3></div><StatusBadge status={loading ? 'LOADING' : record?.status || 'NOT_REQUESTED'} /></div>
      {loading && <p className="report-note">Checking investigation status…</p>}
      {!loading && !error && record?.status === 'NOT_REQUESTED' && <div className="request-row"><p>No report exists for this candidate yet. Request a one-time evidence review.</p><button className="action-button" disabled={requesting} onClick={startInvestigation}>{requesting ? 'Queueing…' : 'Request investigation'}</button></div>}
      {record?.status === 'QUEUED' && <p className="report-note">The evidence review is queued.{record.trigger_reasons?.length ? ` Qualification: ${record.trigger_reasons.map(formatTriggerReason).join(', ')}.` : ''}</p>}
      {record?.status === 'RUNNING' && <p className="report-note">The agent is checking the available evidence sources.</p>}
      {record?.status === 'FAILED' && <div className="request-row"><p>The agent could not complete this review. The event remains available for human review.</p><button className="action-button" disabled={requesting} onClick={startInvestigation}>{requesting ? 'Retrying…' : 'Retry investigation'}</button></div>}
      {error && <p className="report-error" role="alert">{error}</p>}
      {report && <InvestigationFindings report={report} />}
      <section className="human-review" aria-labelledby="human-review-title">
        <div className="human-review-heading"><div><p className="eyebrow">HUMAN REVIEW</p><h4 id="human-review-title">Record an outcome</h4></div><span>{reviewerAuth.session ? `SIGNED IN · ${reviewerAuth.session.email}` : 'INVITED REVIEWER ACCESS REQUIRED'}</span></div>
        {reviewsLoading && <p className="report-note">Checking saved human review…</p>}
        {reviews.length > 0 && <div className="latest-review" role="status"><p>Review outcome saved: <strong>{reviews[0].outcome.replaceAll('_', ' ')}</strong>{reviews[0].reviewed_at_utc && <time dateTime={reviews[0].reviewed_at_utc}> · {formatTimestamp(reviews[0].reviewed_at_utc)}</time>}</p>{reviews[0].notes && reviewerAuth.session && <blockquote>{reviews[0].notes}</blockquote>}{!addingAnotherReview && <button type="button" className="secondary-button" onClick={() => setAddingAnotherReview(true)}>Add another outcome</button>}</div>}
        {reviewError && <p className="report-error" role="alert">Review history unavailable: {reviewError}</p>}
        {!reviewerAuth.session && <p className="reviewer-required">Human review submissions are restricted to invited BurnBlind reviewers. <button type="button" className="text-button" onClick={() => reviewerAuth.openSignIn('Sign in to save a review outcome for this event.')}>Sign in</button></p>}
        {(!reviewsLoading && reviews.length === 0 || addingAnotherReview) && <form onSubmit={saveReview}>
          <label>Outcome<select value={reviewOutcome} onChange={(change) => setReviewOutcome(change.target.value)}><option value="NEEDS_VERIFICATION">Needs verification</option><option value="CONFIRMED">Confirmed by reviewer</option><option value="FALSE_POSITIVE">False positive</option><option value="INSUFFICIENT_EVIDENCE">Insufficient evidence</option></select></label>
          <label>Notes <span>(optional)</span><textarea value={reviewNotes} onChange={(change) => setReviewNotes(change.target.value)} maxLength={1000} rows={2} placeholder="Add a short source-backed note" /></label>
          <button className="action-button" type="submit" disabled={reviewBusy || !reviewerAuth.session}>{reviewBusy ? 'Saving…' : 'Save review outcome'}</button>
        </form>}
      </section>
    </div>
    </div>
  </section>;
}

function ContextCard({ icon, title, state, value, detail, evidenceIds }) {
  const available = ['AVAILABLE', 'OK', 'ESTIMATED', 'AGREEMENT', 'DISAGREEMENT', 'INCONCLUSIVE'].includes(state);
  const loading = !state || state === 'LOADING';
  const failed = state === 'ERROR';
  return <article className={`event-feature-card${available ? ' context-available' : ''}`}>
    <div className="context-card-heading"><span className="context-card-icon">{icon}</span><h4>{title}</h4><span className={`context-state${available ? ' is-available' : ''}`}>{loading ? 'Checking' : available ? (state === 'ESTIMATED' ? 'Estimated' : 'Available') : failed || state === 'UNAVAILABLE' || state === 'INDEPENDENT_OBSERVATION_UNAVAILABLE' ? 'Unavailable' : state === 'NOT_RUN' || !state ? 'Not run' : 'Evidence needed'}</span></div>
    <strong>{available ? value || 'Source record attached' : loading ? 'Checking linked records…' : failed ? 'Could not load this context' : 'No source record attached'}</strong>
    <p>{detail}</p>
    {evidenceIds?.length > 0 && <small>Evidence IDs: {evidenceIds.join(', ')}</small>}
  </article>;
}

function formatSource(source) {
  return source === 'GK2A_AMI' ? 'GK2A AMI' : source.replaceAll('_', ' ');
}

function StatusBadge({ status }) {
  const labels = { NOT_REQUESTED: 'NOT REQUESTED', QUEUED: 'QUEUED', RUNNING: 'IN REVIEW', COMPLETED: 'REPORT READY', FAILED: 'REVIEW FAILED', LOADING: 'CHECKING' };
  return <span className={`investigation-status status-${status.toLowerCase()}`}>{labels[status] || status}</span>;
}

function formatTriggerReason(reason) {
  return ({
    HIGH_PRIORITY: 'high priority score',
    HIGH_UNCERTAINTY: 'high uncertainty with supported likelihood evidence',
    HIGH_BLINDNESS_WITH_MODERATE_FIRE_LIKELIHOOD: 'high monitoring blindness with moderate fire likelihood',
    HIGH_EXPOSURE: 'high estimated exposure',
  })[reason] || reason.replaceAll('_', ' ').toLowerCase();
}

function formatScore(value) {
  return Number.isFinite(value) ? value.toFixed(2) : 'unavailable';
}

function InvestigationFindings({ report }) {
  return <div className="findings">
    <div className="finding-summary"><span className="detail-label">{report.classification?.replaceAll('_', ' ')}</span><p>{report.summary}</p></div>
    {report.evidence?.length > 0 && <section><h4>Evidence reviewed</h4><ul>{report.evidence.map((item) => <li key={item.evidence_id}><span>{item.source}</span><p>{item.summary}</p><code>{item.evidence_id}</code></li>)}</ul></section>}
    {report.contradictions?.length > 0 && <section><h4>Contradictions</h4><ul className="plain-list">{report.contradictions.map((item, index) => <li key={item.explanation || item || index}>{typeof item === 'string' ? item : `${item.explanation} [${item.evidence_ids.join(', ')}]`}</li>)}</ul></section>}
    {report.missing_evidence?.length > 0 && <section><h4>Evidence unavailable</h4><ul className="plain-list">{report.missing_evidence.map((item) => <li key={item}>{item}</li>)}</ul></section>}
    <p className="recommendation"><span>RECOMMENDATION</span><strong>{(report.recommendations || (report.recommended_action ? [report.recommended_action] : [])).map((item) => item.replaceAll('_', ' ')).join(' · ')}</strong><small>Advisory only · a human makes the operational decision.</small></p>
  </div>;
}
