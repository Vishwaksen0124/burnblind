const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

async function request(path, { signal, method = 'GET' } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    signal,
    headers: method === 'POST' ? { 'Content-Type': 'application/json' } : undefined,
  });
  const payload = await response.json();
  if (!response.ok && response.status !== 202) {
    throw new Error(payload.error?.message || `Request failed (${response.status})`);
  }
  return payload;
}

export const getSummary = (signal) => request('/summary', { signal });
export const getEvents = (signal, limit = 100) => request(`/events?limit=${limit}`, { signal });
export const getEvent = (id, signal) => request(`/events/${encodeURIComponent(id)}`, { signal });
export const getInvestigation = (id, signal) => request(`/events/${encodeURIComponent(id)}/investigation`, { signal });
export const requestInvestigation = (id) => request(`/events/${encodeURIComponent(id)}/investigate`, { method: 'POST' });
