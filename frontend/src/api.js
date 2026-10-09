import { getValidReviewerToken } from './auth.js';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';
const MAX_THROTTLE_RETRIES = 4;

async function request(path, { signal, method = 'GET', body, reviewerToken } = {}) {
  let response;
  const validReviewerToken = reviewerToken ? await getValidReviewerToken() : null;
  for (let attempt = 0; ; attempt += 1) {
    const headers = method === 'POST' ? { 'Content-Type': 'application/json' } : {};
    if (validReviewerToken) headers.Authorization = `Bearer ${validReviewerToken}`;
    response = await fetch(`${API_BASE}${path}`, {
      method,
      signal,
      headers: Object.keys(headers).length ? headers : undefined,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (response.status !== 429 || attempt >= MAX_THROTTLE_RETRIES) break;
    await waitBeforeRetry(retryDelay(response, attempt), signal);
  }
  const payload = await response.json();
  if (!response.ok && response.status !== 202) {
    const error = new Error(payload.error?.message || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return payload;
}

function retryDelay(response, attempt) {
  const retryAfter = response.headers.get('Retry-After');
  if (retryAfter) {
    const seconds = Number(retryAfter);
    const retryAt = Number.isFinite(seconds) ? Date.now() + seconds * 1000 : Date.parse(retryAfter);
    if (Number.isFinite(retryAt)) return Math.min(5000, Math.max(0, retryAt - Date.now()));
  }
  return 250 * (2 ** attempt);
}

function waitBeforeRetry(milliseconds, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('The request was aborted.', 'AbortError'));
      return;
    }
    const timer = window.setTimeout(() => {
      signal?.removeEventListener('abort', abort);
      resolve();
    }, milliseconds);
    function abort() {
      window.clearTimeout(timer);
      reject(new DOMException('The request was aborted.', 'AbortError'));
    }
    signal?.addEventListener('abort', abort, { once: true });
  });
}

export const getSummary = (signal) => request('/summary', { signal });
export const getEvents = (signal, limit = 100, cursor) => request(`/events?limit=${limit}${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`, { signal });
export const getActionCenter = (signal, limit = 50, cursor) => request(`/action-center?limit=${limit}${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`, { signal });
export const getMapLayer = (layer, signal) => request(`/map-layers?layer=${encodeURIComponent(layer)}`, { signal });
export const getReplay = (at, signal, limit = 100, cursor) => request(`/replay?at=${encodeURIComponent(at)}&limit=${limit}${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`, { signal });
export const getEvent = (id, signal) => request(`/events/${encodeURIComponent(id)}`, { signal });
export const getInvestigation = (id, signal) => request(`/events/${encodeURIComponent(id)}/investigation`, { signal });
export const getInvestigations = (signal, limit = 50, cursor) => request(`/investigations?limit=${limit}${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`, { signal });
export const requestInvestigation = (id, reviewerToken) => request(`/events/${encodeURIComponent(id)}/investigate`, { method: 'POST', reviewerToken });
export const getReviewOutcomes = (id, signal) => request(`/events/${encodeURIComponent(id)}/review`, { signal });
export const submitReviewOutcome = (id, outcome, notes, reviewerToken) => request(`/events/${encodeURIComponent(id)}/review`, { method: 'POST', body: { outcome, notes }, reviewerToken });
export const getSensorComparison = (id, signal) => request(`/events/${encodeURIComponent(id)}/sensor-comparison`, { signal });
export const getExposure = (id, signal) => request(`/events/${encodeURIComponent(id)}/exposure`, { signal });
export const getEnvironmentalAnalysis = (id, signal) => request(`/events/${encodeURIComponent(id)}/environmental-analysis`, { signal });
export const requestEnvironmentalAnalysis = (id, reviewerToken) => request(`/events/${encodeURIComponent(id)}/environmental-analysis`, { method: 'POST', reviewerToken });
