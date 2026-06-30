window.Pages = window.Pages || {};

Pages.overview = {
  title: 'Overview',
  subtitle: 'Here is what is happening with your network today.',

  async render() {
    const [router, firewall, dhcp, devices] = await Promise.all([
      NinjakuAPI.get('/router'),
      NinjakuAPI.get('/firewall'),
      NinjakuAPI.get('/dhcp'),
      NinjakuAPI.get('/devices')
    ]);

    const deviceList = devices.devices || [];
    const online = deviceList.filter(d => d.status === 'online').length;

    return `
      <div class="hero">
        <div>
          <h2>Good day, admin 👋</h2>
          <p>${router.state === 'running' ? 'Everything looks operational.' : 'Ninjaku needs your attention.'}</p>
        </div>
        <div>
          <button class="icon-button" onclick="Ninjaku.refresh()">↻</button>
          <button class="primary-button" onclick="Ninjaku.applyPolicy()">Apply Policy</button>
        </div>
      </div>

      <section class="grid grid-6" style="margin-bottom:18px">
        ${UI.statCard({ icon: '✓', color: statusColor(router.state), label: 'System Status', value: router.state === 'running' ? 'Healthy' : router.state, sub: 'Router state' })}
        ${UI.statCard({ icon: '◷', color: 'blue', label: 'IPv4 Forward', value: router.ip_forward === '1' ? 'Enabled' : 'Disabled', sub: 'Kernel forwarding' })}
        ${UI.statCard({ icon: '▣', color: 'purple', label: 'Devices Online', value: online, sub: `of ${devices.count || 0} devices` })}
        ${UI.statCard({ icon: '🌐', color: statusColor(router.wan_state), label: 'WAN Status', value: router.wan_state || 'unknown', sub: router.wan || '-' })}
        ${UI.statCard({ icon: '🛡', color: firewall.nft_ok ? 'green' : 'red', label: 'Firewall', value: firewall.nft_ok ? 'OK' : 'Failed', sub: 'nftables' })}
        ${UI.statCard({ icon: '⇄', color: statusColor(dhcp.service), label: 'DHCP', value: dhcp.service || 'unknown', sub: 'dnsmasq' })}
      </section>

      <section class="grid grid-2">
        ${UI.panel('Network Interfaces', `
          <div class="activity-list">
            <div class="activity-item"><div class="activity-dot"></div><div><strong>WAN (${escapeHtml(router.wan)})</strong><br><span>${escapeHtml(router.wan_state)} · upstream interface</span></div><strong>${escapeHtml(router.wan)}</strong></div>
            <div class="activity-item"><div class="activity-dot"></div><div><strong>LAN (${escapeHtml(router.lan)})</strong><br><span>${escapeHtml(router.lan_state)} · DHCP network</span></div><strong>${escapeHtml(router.lan_ip)}</strong></div>
            <div class="activity-item"><div class="activity-dot"></div><div><strong>Firewall</strong><br><span>nftables status</span></div><strong>${firewall.nft_ok ? 'OK' : 'Failed'}</strong></div>
            <div class="activity-item"><div class="activity-dot"></div><div><strong>DHCP</strong><br><span>LAN address assignment</span></div><strong>${escapeHtml(dhcp.service)}</strong></div>
          </div>
        `)}

        ${UI.panel('System Activity', `
          <div class="activity-list">
            <div class="activity-item"><div class="activity-dot"></div><div>Router state is ${escapeHtml(router.state)}</div><span>now</span></div>
            <div class="activity-item"><div class="activity-dot"></div><div>Firewall ruleset checked</div><span>now</span></div>
            <div class="activity-item"><div class="activity-dot"></div><div>${online} device(s) online</div><span>now</span></div>
            <div class="activity-item"><div class="activity-dot"></div><div>DHCP service is ${escapeHtml(dhcp.service)}</div><span>now</span></div>
          </div>
        `)}
      </section>
    `;
  }
};
