window.NinjakuAPI = {
  async request(path, options = {}) {
    const res = await fetch('/api/v1' + path, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error?.message || 'API error');
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
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  }[m]));
}

function statusClass(value) {
  if (['running','active','ok','true','1'].includes(String(value).toLowerCase())) return 'ok';
  if (['waiting_for_lan','inactive','unknown','failed'].includes(String(value).toLowerCase())) return 'warn';
  return '';
}
