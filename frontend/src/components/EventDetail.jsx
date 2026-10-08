import { formatCoordinate, formatTimestamp } from '../lib/eventView.js';

export default function EventDetail({ event, onClose }) {
  return <section className="detail-section panel" aria-labelledby="event-detail-title">
    <div className="detail-heading"><div><p className="eyebrow">CANDIDATE EVENT · SOURCE EVIDENCE</p><h2 id="event-detail-title">Potential thermal detection</h2></div><button className="close-button" onClick={onClose} aria-label="Close event details">×</button></div>
    <div className="detail-grid">
      <div className="detail-block"><span className="detail-label">OBSERVED</span><strong>{formatTimestamp(event.detected_at_utc)}</strong><small>Last observation · {formatTimestamp(event.last_observed_at_utc)}</small></div>
      <div className="detail-block"><span className="detail-label">LOCATION</span><strong>{formatCoordinate(event.latitude, 'N')} · {formatCoordinate(event.longitude, 'E')}</strong><small>Punjab + Haryana replay region</small></div>
      <div className="detail-block"><span className="detail-label">OBSERVED EVIDENCE</span><strong>{event.sources.join(' · ') || 'Source unavailable'}</strong><small>{event.detection_count} grouped {event.detection_count === 1 ? 'detection' : 'detections'}</small></div>
      <div className="detail-block detail-unavailable"><span className="detail-label">ASSESSMENT</span><strong>Not calculated</strong><small>Required features are not available in this replay.</small></div>
    </div>
    <div className="detail-disclosure"><span>EVENT REFERENCE</span><code>{event.event_id}</code><span className="disclosure-separator" /><span>Cross-sensor comparison, exposure estimates, and investigation findings are not available.</span><a className="detail-link" href="#investigations">Investigation status <span aria-hidden="true">↗</span></a></div>
  </section>;
}
