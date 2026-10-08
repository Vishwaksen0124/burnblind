import { useCallback, useEffect, useState } from 'react';
import { getInvestigation, requestInvestigation } from '../api.js';
import { formatCoordinate, formatTimestamp } from '../lib/eventView.js';

const ACTIVE_STATUSES = new Set(['QUEUED', 'RUNNING']);

export default function EventDetail({ event, onClose }) {
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('event');

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
    setActiveTab('event');
    poll();
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
    {report.contradictions?.length > 0 && <section><h4>Contradictions</h4><ul className="plain-list">{report.contradictions.map((item) => <li key={item}>{item}</li>)}</ul></section>}
    {report.missing_evidence?.length > 0 && <section><h4>Evidence unavailable</h4><ul className="plain-list">{report.missing_evidence.map((item) => <li key={item}>{item}</li>)}</ul></section>}
    <p className="recommendation"><span>RECOMMENDATION</span><strong>{report.recommended_action?.replaceAll('_', ' ')}</strong><small>Advisory only · a human makes the operational decision.</small></p>
  </div>;
}
