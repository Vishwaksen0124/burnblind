import { CircleMarker, MapContainer, TileLayer, Tooltip, ZoomControl } from 'react-leaflet';
import { eventLabel, formatTimestamp } from '../lib/eventView.js';

const REGION_BOUNDS = [[28.75, 73.75], [32.75, 77.85]];

export default function CandidateMap({ events = [], className = 'map', interactive = true, zoomControl = true, onEventSelect }) {
  return <MapContainer bounds={REGION_BOUNDS} boundsOptions={{ padding: [18, 18] }} minZoom={6} maxZoom={12} scrollWheelZoom={interactive} dragging={interactive} zoomControl={false} className={className}>
    <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {zoomControl && <ZoomControl position="bottomright" />}
    {events.map((event) => <CircleMarker key={event.event_id} center={[event.latitude, event.longitude]} radius={event.detection_count > 1 ? 7 : 5} pathOptions={{ color: '#ffb020', weight: 1.5, fillColor: '#ff6a1a', fillOpacity: 0.82 }} eventHandlers={interactive && onEventSelect ? { click: () => onEventSelect(event) } : undefined}>
      <Tooltip><strong>{eventLabel(event)}</strong><br />{formatTimestamp(event.detected_at_utc)}</Tooltip>
    </CircleMarker>)}
  </MapContainer>;
}
