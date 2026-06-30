window.Pages = window.Pages || {};

function routerHealth(r) {
  if (r.state === 'running') return { text: 'Healthy', cls: 'ok', hint: 'Router services are running.' };
  if (r.state === 'waiting_for_lan') return { text: 'Waiting for LAN', cls: 'warn', hint: 'LAN interface is missing or disconnected.' };
  return { text: 'Needs Attention', cls: 'fail', hint: 'Router is not fully operational.' };
}

Pages.router = {
  title: 'Router',
  subtitle: 'WAN, LAN, forwarding, NAT and router state',

  async render() {
    const r = await NinjakuAPI.get('/router');
    const health = routerHealth(r);

    return `
      <section class="grid cards">
        <div class="card">
          <span>Router Health</span>
          <strong class="${health.cls}">${health.text}</strong>
          <p>${health.hint}</p>
        </div>
        <div class="card">
          <span>State</span>
          <strong class="${statusClass(r.state)}">${escapeHtml(r.state)}</strong>
          <p>enabled: ${escapeHtml(r.enabled)}</p>
        </div>
        <div class="card">
          <span>WAN</span>
          <strong>${escapeHtml(r.wan)}</strong>
          <p>${escapeHtml(r.wan_state || 'unknown')}</p>
        </div>
        <div class="card">
          <span>LAN</span>
          <strong>${escapeHtml(r.lan)}</strong>
          <p>${escapeHtml(r.lan_state || 'unknown')}</p>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3>Router Control</h3>
          <div>
            <button onclick="RouterActions.enable()">Enable</button>
            <button onclick="RouterActions.applyPolicy()">Apply Policy</button>
            <button class="danger" onclick="RouterActions.disable()">Disable</button>
          </div>
        </div>

        <div class="kv">
          <div><span>WAN Interface</span><strong>${escapeHtml(r.wan)} (${escapeHtml(r.wan_state)})</strong></div>
          <div><span>LAN Interface</span><strong>${escapeHtml(r.lan)} (${escapeHtml(r.lan_state)})</strong></div>
          <div><span>LAN IP</span><strong>${escapeHtml(r.lan_ip)}</strong></div>
          <div><span>DHCP</span><strong class="${statusClass(r.dhcp)}">${escapeHtml(r.dhcp)}</strong></div>
          <div><span>IPv4 Forward</span><strong>${escapeHtml(r.ip_forward)}</strong></div>
          <div><span>NAT</span><strong>${r.ip_forward === '1' ? 'Enabled' : 'Unknown'}</strong></div>
        </div>
      </section>

      ${r.state === 'waiting_for_lan' ? `
        <section class="panel warning-panel">
          <h3 class="warn">LAN Interface Missing</h3>
          <p>Ninjaku is waiting for <strong>${escapeHtml(r.lan)}</strong>. Plug the LAN adapter back in, then Ninjaku daemon will retry restoring router state automatically.</p>
        </section>
      ` : ''}

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
    if (!confirm('Disable router services? SSH on WAN should remain active.')) return;
    await NinjakuAPI.post('/router/disable');
    await Ninjaku.navigate('router');
  },
  async applyPolicy() {
    await NinjakuAPI.post('/policy/apply');
    await Ninjaku.navigate('router');
  }
};
