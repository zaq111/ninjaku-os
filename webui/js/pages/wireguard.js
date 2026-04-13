window.Pages = window.Pages || {};

function shortKey(key) {
  if (!key) return '-';
  if (key.length <= 18) return key;
  return key.slice(0, 8) + '...' + key.slice(-8);
}

Pages.wireguard = {
  title: 'WireGuard',
  subtitle: 'Remote access, peers and future site-to-site tunnels.',

  async render() {
    const data = await NinjakuAPI.get('/wireguard');
    const s = data.server || {};
    const peers = data.peers || [];

    const serverKeyStatus = s.has_private_key && s.public_key;

    const peerRows = peers.map(p => `
      <tr>
        <td>
          <strong>${escapeHtml(p.name)}</strong><br>
          <span class="muted">${escapeHtml(p.id)}</span>
        </td>
        <td>
          ${UI.badge(p.has_private_key ? 'Generated' : 'Missing', p.has_private_key ? 'green' : 'orange')}
        </td>
        <td>${escapeHtml(p.allowed_ips || '-')}</td>
        <td>${escapeHtml(p.endpoint || '-')}</td>
        <td>
          <button class="soft-button" onclick="WireGuardActions.generatePeerKeys('${escapeHtml(p.id)}')">Generate</button>
          <button class="soft-button" ${p.has_private_key ? '' : 'disabled'} onclick="WireGuardActions.exportPeer('${escapeHtml(p.id)}')">Export</button>
          <button class="soft-button" ${p.has_private_key ? '' : 'disabled'} onclick="WireGuardActions.showQr('${escapeHtml(p.id)}')">QR</button>
          <button class="danger-button" onclick="WireGuardActions.deletePeer('${escapeHtml(p.id)}')">Delete</button>
        </td>
      </tr>
    `).join('');

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '◇', color: serverKeyStatus ? 'green' : 'orange', label: 'WireGuard', value: serverKeyStatus ? 'Keys Ready' : 'Framework Ready', sub: data.running ? 'running' : 'not running' })}
        ${UI.statCard({ icon: '⇄', color: 'blue', label: 'Interface', value: s.interface || 'wg0', sub: s.address || '-' })}
        ${UI.statCard({ icon: '◉', color: 'purple', label: 'Port', value: s.listen_port || '51820', sub: 'listen port' })}
        ${UI.statCard({ icon: '▣', color: 'green', label: 'Peers', value: data.peer_count || 0, sub: 'configured peers' })}
      </section>

      ${UI.panel('Server', `
        <div class="form-grid wg-server-grid">
          <div><label>Interface</label><input id="wg-interface" value="${escapeHtml(s.interface || 'wg0')}"></div>
          <div><label>Address</label><input id="wg-address" value="${escapeHtml(s.address || '10.99.0.1/24')}"></div>
          <div><label>Listen Port</label><input id="wg-port" value="${escapeHtml(s.listen_port || '51820')}"></div>
          <div><label>DNS</label><input id="wg-dns" value="${escapeHtml(s.dns || '10.99.0.1')}"></div>
          <div><label>MTU</label><input id="wg-mtu" value="${escapeHtml(s.mtu || '1420')}"></div>
          <div><label>Public Endpoint</label><input id="wg-endpoint" value="${escapeHtml(s.endpoint || '')}" placeholder="vpn.example.com or public IP"></div>
        </div>
        <label class="inline-check" style="margin-top:14px">
          <input type="checkbox" id="wg-enabled" ${s.enabled ? 'checked' : ''}>
          Enable WireGuard configuration
        </label>
      `, `
        <button class="soft-button" onclick="WireGuardActions.generateServerKeys()">${serverKeyStatus ? 'Regenerate Keys' : 'Generate Keys'}</button>
        <button class="primary-button" onclick="WireGuardActions.saveServer()">Save Server</button>
        ${data.running
          ? '<button class="danger-button" onclick="WireGuardActions.stop()">Stop</button><button class="soft-button" onclick="WireGuardActions.restart()">Restart</button>'
          : '<button class="primary-button" onclick="WireGuardActions.apply()">Start / Apply</button>'}
      `)}

      ${UI.panel('Server Keys', `
        <div class="wg-key-box">
          <div>
            <span class="muted">Status</span>
            <strong>${serverKeyStatus ? 'Generated' : 'Missing'}</strong>
          </div>
          <div>
            <span class="muted">Public Key</span>
            <strong>${escapeHtml(shortKey(s.public_key || ''))}</strong>
          </div>
          <button class="soft-button" ${s.public_key ? '' : 'disabled'} onclick="WireGuardActions.copy('${escapeHtml(s.public_key || '')}')">Copy</button>
        </div>
      `)}

      ${UI.panel('Runtime Status', `
        <div class="wg-runtime">
          <div>${UI.badge(data.running ? 'Running' : 'Not Running', data.running ? 'green' : 'orange')}</div>
          <pre>${escapeHtml((data.runtime && data.runtime.wg_show) ? data.runtime.wg_show : 'WireGuard interface is not running.')}</pre>
        </div>
      `)}

      ${UI.panel('Peers', `
        <table class="table">
          <thead><tr><th>Peer</th><th>Keys</th><th>Allowed IPs</th><th>Endpoint</th><th>Actions</th></tr></thead>
          <tbody>${peerRows || '<tr><td colspan="5">No peers yet.</td></tr>'}</tbody>
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
      mtu: document.getElementById('wg-mtu').value.trim(),
      endpoint: document.getElementById('wg-endpoint').value.trim()
    });

    UI.toast('success', 'WireGuard saved', 'Server settings were saved.');
    await Ninjaku.navigate('wireguard');
  },

  async apply() {
    const r = await NinjakuAPI.post('/wireguard/apply');
    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'WireGuard started' : 'WireGuard failed', r.stderr || 'Apply completed.');
    await Ninjaku.navigate('wireguard');
  },

  async stop() {
    const ok = await UI.confirm({
      title: 'Stop WireGuard?',
      message: 'Remote VPN access through this tunnel will be stopped.',
      confirmText: 'Stop',
      danger: true
    });
    if (!ok) return;

    const r = await NinjakuAPI.post('/wireguard/stop');
    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'WireGuard stopped' : 'Stop failed', r.stderr || 'Stop completed.');
    await Ninjaku.navigate('wireguard');
  },

  async restart() {
    const r = await NinjakuAPI.post('/wireguard/restart');
    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'WireGuard restarted' : 'Restart failed', r.stderr || 'Restart completed.');
    await Ninjaku.navigate('wireguard');
  },

  async generateServerKeys() {
    await NinjakuAPI.post('/wireguard/server/generate-keys');
    UI.toast('success', 'Server keys generated', 'WireGuard server keys were updated.');
    await Ninjaku.navigate('wireguard');
  },

  async generatePeerKeys(id) {
    await NinjakuAPI.post('/wireguard/peers/' + encodeURIComponent(id) + '/generate-keys', { preshared: true });
    UI.toast('success', 'Peer keys generated', 'WireGuard peer keys were updated.');
    await Ninjaku.navigate('wireguard');
  },

  async copy(value) {
    if (!value) return;
    await navigator.clipboard.writeText(value);
    UI.toast('success', 'Copied', 'Public key copied to clipboard.');
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

              <label>Endpoint</label>
              <input id="wg-peer-endpoint" placeholder="optional">

              <label>Persistent Keepalive</label>
              <input id="wg-peer-keepalive" value="25">

              <label>Description</label>
              <textarea id="wg-peer-description"></textarea>

              <label class="inline-check">
                <input type="checkbox" id="wg-peer-generate" checked>
                Generate keys automatically
              </label>
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

    const result = await NinjakuAPI.post('/wireguard/peers', {
      name,
      allowed_ips: document.getElementById('wg-peer-allowed').value.trim(),
      endpoint: document.getElementById('wg-peer-endpoint').value.trim(),
      persistent_keepalive: document.getElementById('wg-peer-keepalive').value.trim(),
      description: document.getElementById('wg-peer-description').value.trim()
    });

    if (document.getElementById('wg-peer-generate').checked && result.peer?.id) {
      await NinjakuAPI.post('/wireguard/peers/' + encodeURIComponent(result.peer.id) + '/generate-keys', { preshared: true });
    }

    this.close();
    UI.toast('success', 'Peer saved', 'WireGuard peer was saved.');
    await Ninjaku.navigate('wireguard');
  },

  async exportPeer(id) {
    const r = await NinjakuAPI.get('/wireguard/peers/' + encodeURIComponent(id) + '/config');

    if (!r.ok) {
      UI.toast('error', 'Export failed', r.error || 'Unable to export peer config.');
      return;
    }

    if ((r.config || '').includes('YOUR_PUBLIC_IP_OR_DDNS')) {
      UI.toast('warning', 'Endpoint missing', 'Set peer endpoint before using this config outside LAN.');
    }

    let root = document.getElementById('modal-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'modal-root';
      document.body.appendChild(root);
    }

    root.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal wide-modal">
          <div class="modal-head"><h3>Export Peer Config: ${escapeHtml(r.name || id)}</h3></div>
          <div class="modal-body">
            <p class="muted">Save this config as <strong>${escapeHtml(r.filename || (id + '.conf'))}</strong>.</p>
            <pre id="wg-export-config" class="config-preview">${escapeHtml(r.config || '')}</pre>
          </div>
          <div class="modal-actions">
            <button class="soft-button" onclick="WireGuardActions.close()">Close</button>
            <button class="primary-button" onclick="WireGuardActions.copyConfig()">Copy Config</button>
          </div>
        </div>
      </div>
    `;
  },

  async copyConfig() {
    const text = document.getElementById('wg-export-config')?.innerText || '';
    if (!text) return;
    await navigator.clipboard.writeText(text);
    UI.toast('success', 'Copied', 'WireGuard config copied to clipboard.');
  },

  async showQr(id) {
    let root = document.getElementById('modal-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'modal-root';
      document.body.appendChild(root);
    }

    const src = '/api/v1/wireguard/peers/' + encodeURIComponent(id) + '/qr.svg';

    root.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal">
          <div class="modal-head"><h3>WireGuard QR</h3></div>
          <div class="modal-body">
            <div class="wg-qr-box"><img src="${src}" alt="WireGuard QR"></div>
            <p class="muted">Scan this QR code using the WireGuard mobile app.</p>
          </div>
          <div class="modal-actions">
            <button class="soft-button" onclick="WireGuardActions.close()">Close</button>
          </div>
        </div>
      </div>
    `;
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
