window.Pages = window.Pages || {};

Pages.tailscale = {
  title: 'Tailscale',
  subtitle: 'Remote access for CGNAT/home networks without public IP.',

  async render() {
    const data = await NinjakuAPI.get('/tailscale');
    const svc = data.service || {};

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '◇', color: data.installed ? 'green' : 'orange', label: 'Installed', value: data.installed ? 'Yes' : 'No', sub: 'tailscale binary' })}
        ${UI.statCard({ icon: '●', color: svc.active ? 'green' : 'orange', label: 'Service', value: svc.state || 'unknown', sub: 'tailscaled' })}
        ${UI.statCard({ icon: '⇄', color: data.connected ? 'green' : 'orange', label: 'Connection', value: data.connected ? 'Connected' : 'Disconnected', sub: data.backend_state || '-' })}
        ${UI.statCard({ icon: '▣', color: data.ip ? 'blue' : 'orange', label: 'Tailscale IP', value: data.ip || '-', sub: data.hostname || '-' })}
      </section>

      ${UI.panel('Remote Management', `
        <div class="remote-card-grid">
          <div class="remote-card">
            <span>Status</span>
            <strong>${data.connected ? 'Connected' : (data.backend_state || 'Disconnected')}</strong>
          </div>
          <div class="remote-card">
            <span>Tailscale IP</span>
            <strong>${escapeHtml(data.ip || '-')}</strong>
          </div>
          <div class="remote-card">
            <span>MagicDNS</span>
            <strong>${escapeHtml(data.dns_name || '-')}</strong>
          </div>
          <div class="remote-card">
            <span>User</span>
            <strong>${escapeHtml(data.user || '-')}</strong>
          </div>
        </div>

        <div class="remote-actions">
          <button class="soft-button" ${data.ip ? '' : 'disabled'} onclick="TailscaleActions.copy('${escapeHtml(data.ip || '')}', 'Tailscale IP')">Copy IP</button>
          <button class="soft-button" ${data.dns_name ? '' : 'disabled'} onclick="TailscaleActions.copyDns()">Copy DNS</button>
          <button class="primary-button" ${data.ip ? '' : 'disabled'} onclick="window.open('http://${escapeHtml(data.ip || '')}', '_blank')">Open Web UI</button>
        </div>

        <table class="table" style="margin-top:18px">
          <tbody>
            <tr><th>Installed</th><td>${data.installed ? 'Yes' : 'No'}</td></tr>
            <tr><th>Service</th><td>${escapeHtml(svc.state || 'unknown')}</td></tr>
            <tr><th>Backend State</th><td>${escapeHtml(data.backend_state || '-')}</td></tr>
            <tr><th>Hostname</th><td>${escapeHtml(data.hostname || '-')}</td></tr>
            <tr><th>IP</th><td>${escapeHtml(data.ip || '-')}</td></tr>
            <tr><th>DNS Name</th><td>${escapeHtml(data.dns_name || '-')}</td></tr>
            <tr><th>User</th><td>${escapeHtml(data.user || '-')}</td></tr>
          </tbody>
        </table>
      `, `
        ${data.installed ? '' : '<button class="primary-button" onclick="TailscaleActions.install()">Install Tailscale</button>'}
        ${data.installed && !data.connected ? '<button class="primary-button" onclick="TailscaleActions.up()">Login / Connect</button>' : ''}
        ${data.installed && data.connected ? '<button class="soft-button" onclick="TailscaleActions.down()">Disconnect</button><button class="danger-button" onclick="TailscaleActions.logout()">Logout</button>' : ''}
      `)}

      ${UI.panel('How to use', `
        <p class="muted">
          Tailscale is recommended when this router is behind NAT/CGNAT and has no public IP.
          Install it, login, then access Ninjaku using the Tailscale IP shown above.
        </p>
      `)}
    `;
  }
};

window.TailscaleActions = {
  async copy(value, label = 'Value') {
    if (!value) return;
    await navigator.clipboard.writeText(value);
    UI.toast('success', 'Copied', label + ' copied to clipboard.');
  },

  async copyDns() {
    const data = await NinjakuAPI.get('/tailscale');
    const dns = (data.dns_name || '').replace(/\.$/, '');
    if (!dns) return;
    await navigator.clipboard.writeText(dns);
    UI.toast('success', 'Copied', 'MagicDNS copied to clipboard.');
  },

  async install() {
    UI.toast('info', 'Installing Tailscale', 'This may take a while.');
    const r = await NinjakuAPI.post('/tailscale/install');
    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'Tailscale installed' : 'Install failed', r.stderr || '');
    await Ninjaku.navigate('tailscale');
  },

  async up() {
    UI.busy.show('Connecting to Tailscale...', 'Generating login URL. This may take a few seconds.');
    const r = await NinjakuAPI.post('/tailscale/up', { args: [] });
    UI.busy.hide();

    if (r.login_url) {
      UI.toast('success', 'Login URL generated', 'Open the URL to authorize this router.');
      let root = document.getElementById('modal-root');
      if (!root) {
        root = document.createElement('div');
        root.id = 'modal-root';
        document.body.appendChild(root);
      }

      root.innerHTML = `
        <div class="modal-backdrop">
          <div class="modal">
            <div class="modal-head"><h3>Tailscale Login Required</h3></div>
            <div class="modal-body">
              <p class="muted">Open this URL to authorize Ninjaku Router:</p>
              <pre class="config-preview">${escapeHtml(r.login_url)}</pre>
            </div>
            <div class="modal-actions">
              <button class="soft-button" onclick="TailscaleActions.close()">Close</button>
              <button class="primary-button" onclick="window.open('${r.login_url}', '_blank')">Open Login URL</button>
            </div>
          </div>
        </div>
      `;
      return;
    }

    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'Tailscale started' : 'Tailscale login needed', r.stderr || r.stdout || '');
    await Ninjaku.navigate('tailscale');
  },

  close() {
    const root = document.getElementById('modal-root');
    if (root) root.innerHTML = '';
  },

  async down() {
    const r = await NinjakuAPI.post('/tailscale/down');
    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'Tailscale disconnected' : 'Disconnect failed', r.stderr || '');
    await Ninjaku.navigate('tailscale');
  },

  async logout() {
    const ok = await UI.confirm({
      title: 'Logout Tailscale?',
      message: 'This router will be removed from the current Tailscale session.',
      confirmText: 'Logout',
      danger: true
    });
    if (!ok) return;

    const r = await NinjakuAPI.post('/tailscale/logout');
    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'Tailscale logged out' : 'Logout failed', r.stderr || '');
    await Ninjaku.navigate('tailscale');
  }
};
