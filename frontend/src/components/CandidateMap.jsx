import { CircleMarker, MapContainer, TileLayer, Tooltip, ZoomControl, useMap, useMapEvents } from 'react-leaflet';
import { useMemo, useState } from 'react';
import { eventLabel, formatTimestamp } from '../lib/eventView.js';

const REGION_BOUNDS = [[28.75, 73.75], [32.75, 77.85]];

function clusterEvents(map, events) {
  const projected = events.map((event) => ({
    event,
    point: map.latLngToLayerPoint([event.latitude, event.longitude]),
  }));
  const cellSize = 44;
  const cells = new Map();
  for (const item of projected) {
    const key = `${Math.floor(item.point.x / cellSize)}:${Math.floor(item.point.y / cellSize)}`;
    if (!cells.has(key)) cells.set(key, []);
    cells.get(key).push(item);
  }
  return [...cells.values()].map((items) => ({
    events: items.map(({ event }) => event),
    center: [
      items.reduce((sum, { event }) => sum + event.latitude, 0) / items.length,
      items.reduce((sum, { event }) => sum + event.longitude, 0) / items.length,
    ],
  }));
}

function CandidateClusters({ events, onEventSelect, interactive }) {
  const map = useMap();
  const [revision, setRevision] = useState(0);
  useMapEvents({ moveend: () => setRevision((value) => value + 1), zoomend: () => setRevision((value) => value + 1) });
  const clusters = useMemo(() => clusterEvents(map, events), [map, events, revision]);

  return clusters.map(({ events: members, center }) => {
    const clustered = members.length > 1;
    const handleClick = interactive ? () => {
      if (clustered) map.setView(center, Math.min(map.getZoom() + 2, 14));
      else onEventSelect?.(members[0]);
    } : undefined;
    return <CircleMarker
      key={members.map((event) => event.event_id).join(':')}
      center={center}
      radius={clustered ? Math.min(13, 7 + Math.log2(members.length)) : 5}
      pathOptions={{ color: clustered ? '#ffe0a1' : '#ffc277', weight: clustered ? 2 : 1.5, fillColor: clustered ? '#b95e2d' : '#ff6a1a', fillOpacity: clustered ? 0.92 : 0.82 }}
      eventHandlers={handleClick ? { click: handleClick } : undefined}
    >
      <Tooltip>
        <strong>{clustered ? `${members.length} candidate detections` : eventLabel(members[0])}</strong>
        {clustered ? <><br />Select to zoom in</> : <><br />{formatTimestamp(members[0].detected_at_utc)}</>}
      </Tooltip>
    </CircleMarker>;
  });
}

export default function CandidateMap({ events = [], className = 'map', interactive = true, zoomControl = true, onEventSelect, layerItems = [], activeLayer = 'events' }) {
  return <MapContainer bounds={REGION_BOUNDS} boundsOptions={{ padding: [18, 18] }} minZoom={6} maxZoom={14} scrollWheelZoom={interactive} dragging={interactive} zoomControl={false} className={className}>
    <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {zoomControl && <ZoomControl position="bottomright" />}
    <CandidateClusters events={events} onEventSelect={onEventSelect} interactive={interactive} />
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
