const DATE_FORMAT = new Intl.DateTimeFormat('en-IN', {
  dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kolkata',
});

export function formatTimestamp(value) {
  if (!value) return 'Time unavailable';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Time unavailable' : DATE_FORMAT.format(date);
}

export function eventLabel(event) {
  const latitude = Number(event.latitude);
  const longitude = Number(event.longitude);
  const place = Number.isFinite(latitude) && Number.isFinite(longitude)
    ? `near ${Math.abs(latitude).toFixed(2)}°${latitude < 0 ? 'S' : 'N'}, ${Math.abs(longitude).toFixed(2)}°${longitude < 0 ? 'W' : 'E'}`
    : 'location unavailable';
  return `${event.detection_count > 1 ? 'Repeated detections' : 'Candidate detection'} ${place}`;
}

export function eventSearchText(event) {
  return [event.event_id, event.grid_id, ...(event.sources || [])].join(' ').toLowerCase();
}

export function formatCoordinate(value, hemisphere) {
  return `${Math.abs(value).toFixed(3)}°${value < 0 ? (hemisphere === 'N' ? 'S' : 'W') : hemisphere}`;
}
