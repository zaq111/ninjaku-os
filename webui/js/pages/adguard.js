window.Pages = window.Pages || {};

Pages.adguard = {
  title: 'AdGuard Home',
  subtitle: 'DNS filtering and ad blocking powered by AdGuard Home.',

  async render() {
    const data = await NinjakuAPI.get('/adguard');
    const st = data.status || {};
    const stats = data.stats || {};

    const protection = st.protection_enabled === true ? 'Enabled' : 'Unknown';
    const dnsPort = st.dns_port || '-';

    const installed = data.service && data.service !== "not-found" && data.service !== "unknown" && data.service !== "failed";

    return `
      ${!installed ? UI.panel('Install AdGuard Home', `
        <p>AdGuard Home is not installed yet. Click install to download and register the official AdGuard Home service.</p>
      `, `<button class="primary-button" onclick="AdGuardActions.install()">Install AdGuard Home</button>`) : ''}

      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '🛡', color: statusColor(data.service), label: 'Service', value: data.service || 'unknown', sub: 'AdGuardHome' })}
        ${UI.statCard({ icon: '✓', color: data.api_ok ? 'green' : 'red', label: 'API', value: data.api_ok ? 'Connected' : 'Failed', sub: data.url })}
        ${UI.statCard({ icon: '◉', color: protection === 'Enabled' ? 'green' : 'orange', label: 'Protection', value: protection, sub: 'DNS filter' })}
        ${UI.statCard({ icon: '⇄', color: 'blue', label: 'DNS Port', value: dnsPort, sub: 'AdGuard DNS' })}
      </section>

      ${UI.panel('AdGuard Status', `
        <div class="kv">
          ${UI.kv('URL', data.url)}
          ${UI.kv('Service', data.service || 'unknown')}
          ${UI.kv('Enabled', data.enabled || 'unknown')}
          ${UI.kv('API OK', data.api_ok ? 'yes' : 'no')}
          ${UI.kv('Protection', protection)}
          ${UI.kv('DNS Port', dnsPort)}
        </div>
      `)}

      ${UI.panel('Statistics', `
        <div class="kv">
          ${UI.kv('DNS Queries', stats.num_dns_queries ?? '-')}
          ${UI.kv('Blocked Filtering', stats.num_blocked_filtering ?? '-')}
          ${UI.kv('Replaced Safebrowsing', stats.num_replaced_safebrowsing ?? '-')}
          ${UI.kv('Replaced Parental', stats.num_replaced_parental ?? '-')}
        </div>
      `)}

      ${UI.panel('Raw Status', `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`)}
    `;
  }
};


window.AdGuardActions = {
  async install() {
    if (!confirm('Install AdGuard Home now? This requires internet access and may take a few minutes.')) return;
    await NinjakuAPI.post('/adguard/install');
    await Ninjaku.navigate('adguard');
  }
};
