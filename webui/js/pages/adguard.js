window.Pages = window.Pages || {};

Pages.adguard = {
  title: 'AdGuard Home',
  subtitle: 'DNS filtering and ad blocking integrated with Ninjaku OS.',

  async render() {
    const data = await NinjakuAPI.get('/adguard');
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
        <button class="primary-button" onclick="window.open('/','_blank')">Open AdGuard UI</button>
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

      ${!data.api_ok ? UI.panel('Connection Error', `
        <p class="fail">${escapeHtml(data.api_error || data.stats_error || 'Unable to connect to AdGuard Home API.')}</p>
      `) : ''}
    `;
  }
};
