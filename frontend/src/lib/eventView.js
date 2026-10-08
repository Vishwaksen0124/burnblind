const DATE_FORMAT = new Intl.DateTimeFormat('en-IN', {
  dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kolkata',
});

export function formatTimestamp(value) {
  if (!value) return 'Time unavailable';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Time unavailable' : DATE_FORMAT.format(date);
}

export function eventLabel(event) {
  return event.detection_count > 1 ? 'Repeated thermal detections' : 'Potential thermal detection';
}

export function eventSearchText(event) {
  return [event.event_id, event.grid_id, ...(event.sources || [])].join(' ').toLowerCase();
}

export function formatCoordinate(value, hemisphere) {
  return `${Math.abs(value).toFixed(3)}°${value < 0 ? (hemisphere === 'N' ? 'S' : 'W') : hemisphere}`;
}
