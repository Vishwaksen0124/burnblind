import { useCallback, useEffect, useState } from 'react';
import { getExposure, getInvestigation, getReviewOutcomes, getSensorComparison, requestInvestigation, submitReviewOutcome } from '../api.js';
import { formatCoordinate, formatTimestamp } from '../lib/eventView.js';

const ACTIVE_STATUSES = new Set(['QUEUED', 'RUNNING']);

export default function EventDetail({ event, onClose }) {
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('event');
  const [reviews, setReviews] = useState([]);
  const [reviewOutcome, setReviewOutcome] = useState('NEEDS_VERIFICATION');
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewError, setReviewError] = useState('');
  const [sensorComparison, setSensorComparison] = useState(null);
  const [exposure, setExposure] = useState(null);

  const refresh = useCallback(async (signal) => {
    const value = await getInvestigation(event.event_id, signal);
    setRecord(value);
    return value;
  }, [event.event_id]);

  useEffect(() => {
    const controller = new AbortController();
    let timer;
    const poll = async () => {
      try {
        const value = await refresh(controller.signal);
        setError('');
        if (ACTIVE_STATUSES.has(value.status)) timer = window.setTimeout(poll, 2500);
      } catch (err) {
        if (err.name !== 'AbortError') setError(err.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    setLoading(true);
    setRecord(null);
    setReviews([]);
    setReviewError('');
    setSensorComparison(null);
    setExposure(null);
    setActiveTab('event');
    poll();
    getReviewOutcomes(event.event_id, controller.signal)
      .then((value) => setReviews(value.items || []))
      .catch((err) => { if (err.name !== 'AbortError') setReviewError(err.message); });
    getSensorComparison(event.event_id, controller.signal)
      .then(setSensorComparison)
      .catch((err) => { if (err.name !== 'AbortError') setSensorComparison({ status: 'ERROR', reason: err.message }); });
    getExposure(event.event_id, controller.signal)
      .then(setExposure)
      .catch((err) => { if (err.name !== 'AbortError') setExposure({ status: 'ERROR', reason: err.message }); });
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [refresh]);

  async function startInvestigation() {
    setRequesting(true);
    setError('');
    try {
      const result = await requestInvestigation(event.event_id);
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
    setReviewBusy(true);
    setReviewError('');
    try {
      const value = await submitReviewOutcome(event.event_id, reviewOutcome, reviewNotes);
      setReviews((current) => [value.review, ...current]);
      setReviewNotes('');
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
  return <section className="detail-section panel" aria-labelledby="event-detail-title">
    <div className="detail-heading"><div><p className="eyebrow">CANDIDATE EVENT · SOURCE EVIDENCE</p><h2 id="event-detail-title">Potential thermal detection</h2></div><button className="close-button" onClick={onClose} aria-label="Close event details">×</button></div>
    <div className="detail-tabs" role="tablist" aria-label="Event review sections" onKeyDown={handleTabKeyDown}>
      <button id="event-tab" role="tab" aria-selected={activeTab === 'event'} aria-controls="event-panel" tabIndex={activeTab === 'event' ? 0 : -1} onClick={() => setActiveTab('event')}>Event details</button>
      <button id="investigation-tab" role="tab" aria-selected={activeTab === 'investigation'} aria-controls="investigation-panel" tabIndex={activeTab === 'investigation' ? 0 : -1} onClick={() => setActiveTab('investigation')}>
        Investigation{record?.status === 'FAILED' && <span className="tab-state tab-state-failed">Failed</span>}{record?.status === 'COMPLETED' && <span className="tab-state tab-state-complete">Ready</span>}
      </button>
    </div>
    <div id="event-panel" className="detail-tab-panel" role="tabpanel" aria-labelledby="event-tab" hidden={activeTab !== 'event'}>
      <div className="detail-grid">
        <div className="detail-block"><span className="detail-label">OBSERVED</span><strong>{formatTimestamp(event.detected_at_utc)}</strong><small>Last observation · {formatTimestamp(event.last_observed_at_utc)}</small></div>
        <div className="detail-block"><span className="detail-label">LOCATION</span><strong>{formatCoordinate(event.latitude, 'N')} · {formatCoordinate(event.longitude, 'E')}</strong><small>Punjab + Haryana replay region</small></div>
        <div className="detail-block"><span className="detail-label">OBSERVED EVIDENCE</span><strong>{event.sources.join(' · ') || 'Source unavailable'}</strong><small>{event.detection_count} grouped {event.detection_count === 1 ? 'detection' : 'detections'}</small></div>
        <div className={`detail-block ${event.score_status === 'HEURISTIC_SCORES_AVAILABLE' ? '' : 'detail-unavailable'}`}><span className="detail-label">ASSESSMENT</span><strong>{event.score_status === 'HEURISTIC_SCORES_AVAILABLE' ? 'Heuristic scores' : 'Not calculated'}</strong><small>{event.score_status === 'HEURISTIC_SCORES_AVAILABLE' ? `Fire signal ${formatScore(event.fire_likelihood)} · uncertainty ${formatScore(event.uncertainty)} · priority ${formatScore(event.priority_score)}` : 'Required scoring features are not available.'}</small></div>
      </div>
      <div className="detail-disclosure"><span>EVENT REFERENCE</span><code>{event.event_id}</code><span className="disclosure-separator" /><span>Scores, independent fire confirmation, and population exposure are unavailable for this replay.</span></div>
      <div className="event-feature-grid">
        <section className="event-feature-card"><p className="detail-label">CROSS-SENSOR EVIDENCE</p><strong>{sensorComparison?.result?.status?.replaceAll('_', ' ') || (sensorComparison?.status === 'UNAVAILABLE' ? 'COMPARISON UNAVAILABLE' : 'Loading comparison…')}</strong><p>{sensorComparison?.result?.reason || sensorComparison?.reason || 'Comparison status is unavailable.'}</p>{sensorComparison?.result?.evidence_ids?.length > 0 && <small>Evidence: {sensorComparison.result.evidence_ids.join(', ')}</small>}</section>
        <section className="event-feature-card"><p className="detail-label">POTENTIAL EXPOSURE</p><strong>{exposure?.result?.population_estimate != null ? `${Math.round(exposure.result.population_estimate).toLocaleString()} estimated people` : exposure?.status === 'UNAVAILABLE' ? 'ESTIMATE UNAVAILABLE' : 'Loading estimate…'}</strong><p>{exposure?.result?.source ? `${exposure.result.source} · ${exposure.result.method?.replaceAll('_', ' ')}` : exposure?.reason || 'No sourced estimate is attached.'}</p>{exposure?.result?.limitations?.slice(0, 2).map((item) => <small key={item}>{item}</small>)}</section>
      </div>
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
        <div className="human-review-heading"><div><p className="eyebrow">HUMAN REVIEW</p><h4 id="human-review-title">Record an outcome</h4></div><span>PUBLIC DEMO · SUBMITTER NOT AUTHENTICATED</span></div>
        {reviews.length > 0 && <p className="latest-review">Latest outcome: <strong>{reviews[0].outcome.replaceAll('_', ' ')}</strong>{reviews[0].reviewed_at_utc && <time dateTime={reviews[0].reviewed_at_utc}> · {formatTimestamp(reviews[0].reviewed_at_utc)}</time>}</p>}
        {reviewError && <p className="report-error" role="alert">Review history unavailable: {reviewError}</p>}
        <form onSubmit={saveReview}>
          <label>Outcome<select value={reviewOutcome} onChange={(change) => setReviewOutcome(change.target.value)}><option value="NEEDS_VERIFICATION">Needs verification</option><option value="CONFIRMED">Confirmed by reviewer</option><option value="FALSE_POSITIVE">False positive</option><option value="INSUFFICIENT_EVIDENCE">Insufficient evidence</option></select></label>
          <label>Notes <span>(optional)</span><textarea value={reviewNotes} onChange={(change) => setReviewNotes(change.target.value)} maxLength={1000} rows={2} placeholder="Add a short source-backed note" /></label>
          <button className="action-button" type="submit" disabled={reviewBusy}>{reviewBusy ? 'Saving…' : 'Save review outcome'}</button>
        </form>
      </section>
    </div>
    </div>
  </section>;
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
