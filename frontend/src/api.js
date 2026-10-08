const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';
const MAX_THROTTLE_RETRIES = 4;

async function request(path, { signal, method = 'GET' } = {}) {
  let response;
  for (let attempt = 0; ; attempt += 1) {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      signal,
      headers: method === 'POST' ? { 'Content-Type': 'application/json' } : undefined,
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
export const getEvents = (signal, limit = 100) => request(`/events?limit=${limit}`, { signal });
export const getEvent = (id, signal) => request(`/events/${encodeURIComponent(id)}`, { signal });
export const getInvestigation = (id, signal) => request(`/events/${encodeURIComponent(id)}/investigation`, { signal });
export const requestInvestigation = (id) => request(`/events/${encodeURIComponent(id)}/investigate`, { method: 'POST' });
