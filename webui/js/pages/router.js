window.Pages = window.Pages || {};

Pages.router = {
  title: 'Router',
  subtitle: 'WAN, LAN, forwarding, NAT and router state.',

  async render() {
    const r = await NinjakuAPI.get('/router');

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '✓', color: statusColor(r.state), label: 'Router Health', value: r.state, sub: 'Current state' })}
        ${UI.statCard({ icon: '🌐', color: statusColor(r.wan_state), label: 'WAN', value: r.wan, sub: r.wan_state })}
        ${UI.statCard({ icon: '⛓', color: statusColor(r.lan_state), label: 'LAN', value: r.lan, sub: r.lan_state })}
        ${UI.statCard({ icon: '⇄', color: statusColor(r.dhcp), label: 'DHCP', value: r.dhcp, sub: 'dnsmasq' })}
      </section>

      ${UI.panel('Router Control', `
        <div class="kv">
          ${UI.kv('State', r.state)}
          ${UI.kv('Enabled', r.enabled)}
          ${UI.kv('IPv4 Forward', r.ip_forward)}
          ${UI.kv('WAN Interface', `${r.wan} (${r.wan_state})`)}
          ${UI.kv('LAN Interface', `${r.lan} (${r.lan_state})`)}
          ${UI.kv('LAN IP', r.lan_ip)}
        </div>
      `, `
        <button class="primary-button" onclick="RouterActions.enable()">Enable</button>
        <button class="soft-button" onclick="RouterActions.applyPolicy()">Apply Policy</button>
        <button class="danger-button" onclick="RouterActions.disable()">Disable</button>
      `)}

      ${r.state === 'waiting_for_lan' ? UI.panel('LAN Interface Missing', `
        <p>Ninjaku is waiting for <strong>${escapeHtml(r.lan)}</strong>. Plug the LAN adapter back in and ninjakud will retry restoring the router automatically.</p>
      `) : ''}

      ${UI.panel('Routes', `<pre>${escapeHtml(r.routes)}</pre>`)}
      ${UI.panel('Interfaces', `<pre>${escapeHtml(r.interfaces)}</pre>`)}
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
  },
  async applyPolicy() {
    await NinjakuAPI.post('/policy/apply');
    await Ninjaku.navigate('router');
  }
};
