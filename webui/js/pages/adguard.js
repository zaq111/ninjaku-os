window.Pages = window.Pages || {};

Pages.adguard = {
  title: 'AdGuard Home',
  subtitle: 'DNS filtering and ad blocking integrated with Ninjaku OS.',

  async render() {
    const [data, querylogData] = await Promise.all([
      NinjakuAPI.get('/adguard'),
      NinjakuAPI.get('/adguard/querylog?limit=10')
    ]);
    const st = data.status || {};
    const stats = data.stats || {};

    const protectionEnabled = st.protection_enabled === true;
    const running = st.running === true;
    const queries = stats.num_dns_queries ?? 0;
    const blocked = stats.num_blocked_filtering ?? 0;
    const blockRate = queries > 0 ? ((blocked / queries) * 100).toFixed(1) + '%' : '0%';

    const topDomains = (stats.top_queried_domains || []).slice(0, 8).map(item => {
      const domain = Object.keys(item)[0];
      const count = item[domain];
      return `<div class="activity-item"><div class="activity-dot"></div><div>${escapeHtml(domain)}</div><strong>${count}</strong></div>`;
    }).join('');

    const topBlocked = (stats.top_blocked_domains || []).slice(0, 8).map(item => {
      const domain = Object.keys(item)[0];
      const count = item[domain];
      return `<div class="activity-item"><div class="activity-dot"></div><div>${escapeHtml(domain)}</div><strong>${count}</strong></div>`;
    }).join('');

    const qlog = ((querylogData.data || {}).data || []).slice(0, 10);
    const qrows = qlog.map(q => `
      <tr>
        <td><strong>${escapeHtml(q.question?.name || '-')}</strong></td>
        <td>${escapeHtml(q.client || '-')}</td>
        <td>${UI.badge(q.reason || 'allowed', q.reason ? 'orange' : 'green')}</td>
        <td>${escapeHtml(q.time || '-')}</td>
      </tr>
    `).join('');

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '🛡', color: running ? 'green' : 'red', label: 'Service', value: data.service || 'unknown', sub: 'AdGuardHome' })}
        ${UI.statCard({ icon: '✓', color: protectionEnabled ? 'green' : 'orange', label: 'Protection', value: protectionEnabled ? 'Enabled' : 'Disabled', sub: 'DNS filtering' })}
        ${UI.statCard({ icon: '⇄', color: 'blue', label: 'DNS Queries', value: queries, sub: 'recent stats window' })}
        ${UI.statCard({ icon: '×', color: blocked > 0 ? 'red' : 'purple', label: 'Blocked', value: blocked, sub: `${blockRate} blocked` })}
      </section>

      ${UI.panel('AdGuard Home Status', `
        <div class="kv">
          ${UI.kv('API', data.api_ok ? 'Connected' : 'Failed')}
          ${UI.kv('Version', st.version || '-')}
          ${UI.kv('HTTP Port', st.http_port || '-')}
          ${UI.kv('DNS Port', st.dns_port || '-')}
          ${UI.kv('Protection', protectionEnabled ? 'Enabled' : 'Disabled')}
          ${UI.kv('DNS Addresses', (st.dns_addresses || []).join(', ') || '-')}
        </div>
      `, `
        <button class="primary-button" onclick="AdGuardActions.openUI()">Open AdGuard UI</button>
        ${protectionEnabled
          ? '<button class="danger-button" onclick="AdGuardActions.disable()">Disable Protection</button>'
          : '<button class="primary-button" onclick="AdGuardActions.enable()">Enable Protection</button>'}
        <button class="soft-button" onclick="AdGuardActions.updateFilters()">Update Filters</button>
        <button class="soft-button" onclick="Ninjaku.refresh()">Refresh</button>
      `)}

      <section class="grid grid-2">
        ${UI.panel('Top Queried Domains', `
          <div class="activity-list">
            ${topDomains || '<p>No query data yet.</p>'}
          </div>
        `)}

        ${UI.panel('Top Blocked Domains', `
          <div class="activity-list">
            ${topBlocked || '<p>No blocked data yet.</p>'}
          </div>
        `)}
      </section>

      ${UI.panel('Recent DNS Queries', `
        <table class="table">
          <thead><tr><th>Domain</th><th>Client</th><th>Status</th><th>Time</th></tr></thead>
          <tbody>${qrows || '<tr><td colspan="4">No DNS queries yet.</td></tr>'}</tbody>
        </table>
      `)}

      ${!data.api_ok ? UI.panel('Connection Error', `
        <p class="fail">${escapeHtml(data.api_error || data.stats_error || 'Unable to connect to AdGuard Home API.')}</p>
      `) : ''}
    `;
  }
};


window.AdGuardActions = {
  openUI() {
    window.open(window.location.protocol + '//' + window.location.hostname + ':3000/', '_blank');
  },

  async enable() {
    await NinjakuAPI.post('/adguard/protection', { enabled: true });
    UI.toast('success', 'AdGuard enabled', 'DNS protection is now enabled.');
    await Ninjaku.navigate('adguard');
  },

  async updateFilters() {
    UI.toast('info', 'Updating filters', 'AdGuard filter update started.');
    await NinjakuAPI.post('/adguard/update-filters');
    UI.toast('success', 'Filters updated', 'AdGuard filter lists were refreshed.');
    await Ninjaku.navigate('adguard');
  },

  async disable() {
    const ok = await UI.confirm({
      title: 'Disable AdGuard protection?',
      message: 'DNS filtering will stop until protection is enabled again.',
      confirmText: 'Disable',
      danger: true
    });

    if (!ok) return;

    await NinjakuAPI.post('/adguard/protection', { enabled: false });
    UI.toast('success', 'AdGuard disabled', 'DNS protection is now disabled.');
    await Ninjaku.navigate('adguard');
  }
};
