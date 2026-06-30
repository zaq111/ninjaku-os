window.Pages = window.Pages || {};

Pages.router = {
  title: 'Router',
  subtitle: 'WAN, LAN, forwarding, NAT and router state',

  async render() {
    const r = await NinjakuAPI.get('/router');

    return `
      <section class="panel">
        <div class="panel-head">
          <h3>Router Control</h3>
          <div>
            <button onclick="RouterActions.enable()">Enable</button>
            <button class="danger" onclick="RouterActions.disable()">Disable</button>
          </div>
        </div>
        <div class="kv">
          <div><span>State</span><strong class="${statusClass(r.state)}">${escapeHtml(r.state)}</strong></div>
          <div><span>Enabled</span><strong>${escapeHtml(r.enabled)}</strong></div>
          <div><span>IPv4 Forward</span><strong>${escapeHtml(r.ip_forward)}</strong></div>
          <div><span>WAN</span><strong>${escapeHtml(r.wan)} (${escapeHtml(r.wan_state)})</strong></div>
          <div><span>LAN</span><strong>${escapeHtml(r.lan)} (${escapeHtml(r.lan_state)})</strong></div>
          <div><span>LAN IP</span><strong>${escapeHtml(r.lan_ip)}</strong></div>
          <div><span>DHCP</span><strong class="${statusClass(r.dhcp)}">${escapeHtml(r.dhcp)}</strong></div>
        </div>
      </section>

      <section class="panel">
        <h3>Routes</h3>
        <pre>${escapeHtml(r.routes)}</pre>
      </section>

      <section class="panel">
        <h3>Interfaces</h3>
        <pre>${escapeHtml(r.interfaces)}</pre>
      </section>
    `;
  }
};

window.RouterActions = {
  async enable() {
    await NinjakuAPI.post('/router/enable');
    await Ninjaku.navigate('router');
  },
  async disable() {
    if (!confirm('Disable router services?')) return;
    await NinjakuAPI.post('/router/disable');
    await Ninjaku.navigate('router');
  }
};
