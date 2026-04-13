window.Pages = window.Pages || {};

Pages.wireguard = {
  title: 'WireGuard',
  subtitle: 'VPN framework for remote access, peers and future site-to-site tunnels.',

  async render() {
    const data = await NinjakuAPI.get('/wireguard');
    const s = data.server || {};
    const peers = data.peers || [];

    const peerRows = peers.map(p => `
      <tr>
        <td><strong>${escapeHtml(p.name)}</strong><br><span class="muted">${escapeHtml(p.id)}</span></td>
        <td>${UI.badge(p.enabled ? 'enabled' : 'disabled', p.enabled ? 'green' : 'orange')}</td>
        <td>${escapeHtml(p.allowed_ips || '-')}</td>
        <td>${escapeHtml(p.endpoint || '-')}</td>
        <td>${escapeHtml(p.persistent_keepalive || '-')}</td>
        <td><button class="danger-button" onclick="WireGuardActions.deletePeer('${escapeHtml(p.id)}')">Delete</button></td>
      </tr>
    `).join('');

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '◇', color: s.enabled ? 'green' : 'orange', label: 'WireGuard', value: s.enabled ? 'Enabled' : 'Disabled', sub: 'framework phase' })}
        ${UI.statCard({ icon: '⇄', color: 'blue', label: 'Interface', value: s.interface || 'wg0', sub: s.address || '-' })}
        ${UI.statCard({ icon: '◉', color: 'purple', label: 'Port', value: s.listen_port || '51820', sub: 'listen port' })}
        ${UI.statCard({ icon: '▣', color: 'green', label: 'Peers', value: data.peer_count || 0, sub: 'configured peers' })}
      </section>

      ${UI.panel('Server', `
        <div class="form-grid qos-form">
          <input id="wg-interface" value="${escapeHtml(s.interface || 'wg0')}" placeholder="Interface">
          <input id="wg-address" value="${escapeHtml(s.address || '10.99.0.1/24')}" placeholder="Address">
          <input id="wg-port" value="${escapeHtml(s.listen_port || '51820')}" placeholder="Listen port">
          <input id="wg-dns" value="${escapeHtml(s.dns || '10.99.0.1')}" placeholder="DNS">
          <input id="wg-mtu" value="${escapeHtml(s.mtu || '1420')}" placeholder="MTU">
        </div>
        <label class="inline-check" style="margin-top:14px">
          <input type="checkbox" id="wg-enabled" ${s.enabled ? 'checked' : ''}>
          Enable WireGuard configuration
        </label>
      `, `<button class="primary-button" onclick="WireGuardActions.saveServer()">Save Server</button>`)}

      ${UI.panel('Peers', `
        <table class="table">
          <thead><tr><th>Peer</th><th>Status</th><th>Allowed IPs</th><th>Endpoint</th><th>Keepalive</th><th>Action</th></tr></thead>
          <tbody>${peerRows || '<tr><td colspan="6">No peers yet.</td></tr>'}</tbody>
        </table>
      `, `<button class="primary-button" onclick="WireGuardActions.addPeer()">Add Peer</button>`)}
    `;
  }
};

window.WireGuardActions = {
  async saveServer() {
    await NinjakuAPI.post('/wireguard/server', {
      enabled: document.getElementById('wg-enabled').checked,
      interface: document.getElementById('wg-interface').value.trim(),
      address: document.getElementById('wg-address').value.trim(),
      listen_port: document.getElementById('wg-port').value.trim(),
      dns: document.getElementById('wg-dns').value.trim(),
      mtu: document.getElementById('wg-mtu').value.trim()
    });

    UI.toast('success', 'WireGuard saved', 'Server framework settings were saved.');
    await Ninjaku.navigate('wireguard');
  },

  addPeer() {
    let root = document.getElementById('modal-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'modal-root';
      document.body.appendChild(root);
    }

    root.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal">
          <div class="modal-head"><h3>Add WireGuard Peer</h3></div>
          <div class="modal-body">
            <div class="form-stack">
              <label>Name</label>
              <input id="wg-peer-name" placeholder="Laptop">

              <label>Allowed IPs</label>
              <input id="wg-peer-allowed" placeholder="10.99.0.2/32">

              <label>Public Key</label>
              <input id="wg-peer-public" placeholder="Public key">

              <label>Endpoint</label>
              <input id="wg-peer-endpoint" placeholder="optional">

              <label>Description</label>
              <textarea id="wg-peer-description"></textarea>
            </div>
          </div>
          <div class="modal-actions">
            <button class="soft-button" onclick="WireGuardActions.close()">Cancel</button>
            <button class="primary-button" onclick="WireGuardActions.savePeer()">Save Peer</button>
          </div>
        </div>
      </div>
    `;
  },

  close() {
    const root = document.getElementById('modal-root');
    if (root) root.innerHTML = '';
  },

  async savePeer() {
    const name = document.getElementById('wg-peer-name').value.trim();

    if (!name) {
      UI.toast('error', 'Name required', 'Peer name is required.');
      return;
    }

    await NinjakuAPI.post('/wireguard/peers', {
      name,
      allowed_ips: document.getElementById('wg-peer-allowed').value.trim(),
      public_key: document.getElementById('wg-peer-public').value.trim(),
      endpoint: document.getElementById('wg-peer-endpoint').value.trim(),
      description: document.getElementById('wg-peer-description').value.trim()
    });

    this.close();
    UI.toast('success', 'Peer saved', 'WireGuard peer was saved.');
    await Ninjaku.navigate('wireguard');
  },

  async deletePeer(id) {
    const ok = await UI.confirm({
      title: 'Delete WireGuard peer?',
      message: 'This peer will be removed from the framework database.',
      confirmText: 'Delete',
      danger: true
    });

    if (!ok) return;

    await NinjakuAPI.delete('/wireguard/peers/' + encodeURIComponent(id));
    UI.toast('success', 'Peer deleted', 'WireGuard peer was removed.');
    await Ninjaku.navigate('wireguard');
  }
};
