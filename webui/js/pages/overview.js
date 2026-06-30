window.Pages = window.Pages || {};

Pages.overview = {
  title: 'Overview',
  subtitle: 'System overview and live router status',

  async render() {
    const [router, firewall, dhcp, devices] = await Promise.all([
      NinjakuAPI.get('/router'),
      NinjakuAPI.get('/firewall'),
      NinjakuAPI.get('/dhcp'),
      NinjakuAPI.get('/devices')
    ]);

    return `
      <section class="grid cards">
        <div class="card"><span>Router State</span><strong class="${statusClass(router.state)}">${escapeHtml(router.state)}</strong><p>${escapeHtml(router.wan)} → ${escapeHtml(router.lan)}</p></div>
        <div class="card"><span>Firewall</span><strong class="${firewall.nft_ok ? 'ok' : 'fail'}">${firewall.nft_ok ? 'OK' : 'FAILED'}</strong><p>IPv4 forward: ${escapeHtml(firewall.ip_forward)}</p></div>
        <div class="card"><span>DHCP</span><strong class="${statusClass(dhcp.service)}">${escapeHtml(dhcp.service)}</strong><p>dnsmasq</p></div>
        <div class="card"><span>Devices</span><strong>${devices.count || 0}</strong><p>known devices</p></div>
      </section>

      <section class="panel">
        <h3>Quick Router Summary</h3>
        <div class="kv">
          <div><span>WAN</span><strong>${escapeHtml(router.wan)} (${escapeHtml(router.wan_state)})</strong></div>
          <div><span>LAN</span><strong>${escapeHtml(router.lan)} (${escapeHtml(router.lan_state)})</strong></div>
          <div><span>LAN IP</span><strong>${escapeHtml(router.lan_ip)}</strong></div>
        </div>
      </section>
    `;
  }
};
