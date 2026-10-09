import { CircleMarker, MapContainer, TileLayer, Tooltip, ZoomControl } from 'react-leaflet';
import { eventLabel, formatTimestamp } from '../lib/eventView.js';

const REGION_BOUNDS = [[28.75, 73.75], [32.75, 77.85]];

export default function CandidateMap({ events = [], className = 'map', interactive = true, zoomControl = true, onEventSelect, layerItems = [], activeLayer = 'events' }) {
  return <MapContainer bounds={REGION_BOUNDS} boundsOptions={{ padding: [18, 18] }} minZoom={6} maxZoom={12} scrollWheelZoom={interactive} dragging={interactive} zoomControl={false} className={className}>
    <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {zoomControl && <ZoomControl position="bottomright" />}
    {events.map((event) => <CircleMarker key={event.event_id} center={[event.latitude, event.longitude]} radius={event.detection_count > 1 ? 7 : 5} pathOptions={{ color: '#ffb020', weight: 1.5, fillColor: '#ff6a1a', fillOpacity: 0.82 }} eventHandlers={interactive && onEventSelect ? { click: () => onEventSelect(event) } : undefined}>
      <Tooltip><strong>{eventLabel(event)}</strong><br />{formatTimestamp(event.detected_at_utc)}</Tooltip>
    </CircleMarker>)}
    {layerItems.map((item) => {
      const color = activeLayer === 'sensor-disagreement' ? '#d65b47' : activeLayer === 'exposure' ? '#e5b45f' : '#a888d8';
      const raw = item.value?.score ?? item.value?.population_estimate;
      const label = item.value?.status === 'DISAGREEMENT' ? 'Sensor disagreement' : item.value?.score != null ? `Monitoring blindness score ${Number(item.value.score).toFixed(2)}` : item.value?.population_estimate != null ? `Estimated potential exposure ${Number(item.value.population_estimate).toLocaleString()}` : item.value?.status || 'Sourced feature';
      const sourceEvent = events.find((event) => event.event_id === item.event_id);
      return <CircleMarker key={`${activeLayer}-${item.event_id}`} center={[item.latitude, item.longitude]} radius={raw == null ? 8 : 7 + Math.min(6, Math.sqrt(Number(raw)))} pathOptions={{ color, weight: 2, fillColor: color, fillOpacity: 0.35 }} eventHandlers={interactive && onEventSelect && sourceEvent ? { click: () => onEventSelect(sourceEvent) } : undefined}>
        <Tooltip><strong>{label}</strong><br />{formatTimestamp(item.detected_at_utc)}</Tooltip>
      </CircleMarker>;
    })}
  </MapContainer>;
}
