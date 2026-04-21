// Boxing Analytics Web — API client
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const API = {
  analyzeVideo: async (file, onProgress) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/boxing/videos/upload`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json();
  },

  uploadBaseline: async (file) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/boxing/baseline`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json();
  },

  listTestRuns: async (limit = 20) => {
    const res = await fetch(`${BASE}/boxing/test-runs?limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  },

  getStatus: async () => {
    const res = await fetch(`${BASE}/boxing/status`);
    if (!res.ok) return null;
    return res.json();
  },
};

export function createWebSocket(sessionId, userId = 'web-tester', onMessage, onClose) {
  const url = `${WS_BASE}/boxing/ws/jab`;
  const ws = new WebSocket(url);

  ws.onopen = () => {
    console.log('[WS] connected');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {}
  };

  ws.onclose = (e) => {
    console.log('[WS] closed', e.code);
    onClose?.();
  };

  ws.onerror = (e) => console.error('[WS] error', e);

  const send = (payload) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ ...payload, user_id: userId, session_id: sessionId }));
    }
  };

  const close = () => ws.close();

  return { send, close, ws };
}
