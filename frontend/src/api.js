const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

async function request(path, signal) {
  const response = await fetch(`${API_BASE}${path}`, { signal });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error?.message || `Request failed (${response.status})`);
  return payload;
}

export const getSummary = (signal) => request('/summary', signal);
export const getEvents = (signal, limit = 100) => request(`/events?limit=${limit}`, signal);
export const getEvent = (id, signal) => request(`/events/${encodeURIComponent(id)}`, signal);
