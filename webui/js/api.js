window.NinjakuAPI = {
  async request(path, options = {}) {
    const res = await fetch('/api/v1' + path, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });

    const json = await res.json();

    if (!json.success) {
      throw new Error(json.error?.message || 'API error');
    }

    return json.data;
  },

  get(path) {
    return this.request(path);
  },

  post(path, body = {}) {
    return this.request(path, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  delete(path) {
    return this.request(path, { method: 'DELETE' });
  }
};

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, m => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }[m]));
}

function statusColor(value) {
  const v = String(value || '').toLowerCase();
  if (['running', 'active', 'ok', 'online', 'connected', 'healthy', 'true', '1'].includes(v)) return 'green';
  if (['waiting_for_lan', 'unknown', 'inactive', 'restoring'].includes(v)) return 'orange';
  if (['failed', 'offline', 'error', 'down'].includes(v)) return 'red';
  return 'blue';
}

function statusClass(value) {
  const c = statusColor(value);
  if (c === 'green') return 'ok';
  if (c === 'orange') return 'warn';
  if (c === 'red') return 'fail';
  return '';
}
