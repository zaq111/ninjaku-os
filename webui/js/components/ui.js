window.UI = {
  icon(name) {
    const icons = {
      overview: '⌂',
      router: '⌁',
      devices: '▣',
      policy: '♢',
      profiles: '♧',
      settings: '⚙',
      firewall: '🛡',
      dns_filter: '🛡',
      dhcp: '⇄',
      network: '☍',
      healthy: '✓',
      uptime: '◷',
      cpu: '◉',
      memory: '▣',
      wan: '🌐',
      lan: '⛓'
    };
    return icons[name] || '•';
  },

  badge(text, color = '') {
    return `<span class="badge ${color}">${escapeHtml(text)}</span>`;
  },

  statCard({ icon = '•', color = 'blue', label = '', value = '', sub = '' }) {
    return `
      <div class="card">
        <div class="card-icon icon-${color}">${icon}</div>
        <div>
          <small>${escapeHtml(label)}</small>
          <strong>${escapeHtml(value)}</strong>
          <span>${escapeHtml(sub)}</span>
        </div>
      </div>
    `;
  },

  kv(label, value) {
    return `<div class="kv-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
  },

  panel(title, body, action = '') {
    return `
      <section class="panel">
        <div class="panel-head">
          <h3>${escapeHtml(title)}</h3>
          ${action}
        </div>
        ${body}
      </section>
    `;
  }
};
