window.Pages = window.Pages || {};

function qosBadge(d) {
  if (!d.qos_enabled) {
    return '<span class="muted">QoS off</span>';
  }

  const mode = d.qos_mode || 'priority';

  if (mode === 'limiter') {
    const down = String(d.qos_download || '0').replace(/mbit|mbps/gi, '') || '0';
    const up = String(d.qos_upload || '0').replace(/mbit|mbps/gi, '') || '0';
    return `${UI.badge('Limiter ' + down + '/' + up + ' Mbps', 'orange')}<br><small>${escapeHtml(d.qos_queue_label || 'Limiter scheduling')}</small>`;
  }

  return `${UI.badge('CAKE Marking', 'blue')}<br><small>Global application/protocol rules</small>`;
}

function deviceIcon(d) {
  const name = `${d.hostname || ''} ${d.alias || ''}`.toLowerCase();
  if (name.includes('android') || name.includes('iphone') || name.includes('samsung') || name.includes('phone')) return '📱';
  if (name.includes('tv')) return '📺';
  if (name.includes('esp') || name.includes('iot')) return '💡';
  if (name.includes('printer')) return '🖨';
  if (name.includes('laptop')) return '💻';
  if (name.includes('desktop') || name.includes('pc')) return '🖥';
  return '▣';
}

Pages.devices = {
  title: 'Devices',
  subtitle: 'LAN clients, profiles and effective policies.',

  async render() {
    const [data, profilesData, leasesData] = await Promise.all([
      NinjakuAPI.get('/devices'),
      NinjakuAPI.get('/profiles'),
      NinjakuAPI.get('/leases')
    ]);

    DeviceActions.devices = data.devices || [];
    DeviceActions.profiles = profilesData.profiles || [];
    DeviceActions.leases = leasesData.leases || [];

    const devices = DeviceActions.devices;
    const online = data.online ?? devices.filter(d => d.status === 'online').length;
    const offline = data.offline ?? devices.filter(d => d.status === 'offline').length;

    const rows = devices.map(d => `
      <tr>
        <td>${deviceIcon(d)} <strong>${escapeHtml(d.alias || d.hostname || 'Unknown')}</strong></td>
        <td>${escapeHtml(d.ip || '')}</td>
        <td>${escapeHtml(d.mac || '')}</td>
        <td>${UI.badge(d.profile || 'default', 'blue')}</td>
        <td>${UI.badge(d.status || 'unknown', statusColor(d.status))}</td>
        <td>${escapeHtml(d.last_seen_age || '-')}</td>
        <td>${escapeHtml(d.qos_label || d.policy_bandwidth || '')}<br><small>${escapeHtml(d.qos_queue_label || '')}</small></td>
        <td>
          <button class="soft-button" onclick="DeviceActions.edit('${escapeHtml(d.mac)}')">Edit</button>
        </td>
      </tr>
    `).join('');

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '▣', color: 'blue', label: 'Total Devices', value: devices.length, sub: 'known clients' })}
        ${UI.statCard({ icon: '✓', color: 'green', label: 'Online', value: online, sub: 'active now' })}
        ${UI.statCard({ icon: '×', color: 'red', label: 'Offline', value: offline, sub: 'not visible' })}
        ${UI.statCard({ icon: '♢', color: 'purple', label: 'Profiles', value: new Set(devices.map(d => d.profile)).size, sub: 'used profiles' })}
      </section>

      ${UI.panel('Recent Devices', `
        <table class="table">
          <thead><tr><th>Device</th><th>IP Address</th><th>MAC</th><th>Profile</th><th>Status</th><th>Last Seen</th><th>QoS</th><th>Action</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="8">No devices found.</td></tr>'}</tbody>
        </table>
      `, `<button class="primary-button" onclick="DeviceActions.sync()">Sync</button>`)}
    `;
  }
};

window.DeviceActions = {
  devices: [],
  profiles: [],

  async sync() {
    await NinjakuAPI.post('/devices/sync');
    UI.toast('success', 'Devices synced', 'Device inventory was refreshed.');
    await Ninjaku.navigate('devices');
  },

  async edit(mac) {
    const d = this.devices.find(x => x.mac === mac);
    if (!d) return UI.toast('error', 'Device not found', mac);

    let dnsRows = '';
    try {
      const q = await NinjakuAPI.get('/adguard/querylog?limit=8&client=' + encodeURIComponent(d.ip || ''));
      const logs = ((q.data || {}).data || []).slice(0, 8);
      dnsRows = logs.map(item => `
        <tr>
          <td>${escapeHtml(item.question?.name || '-')}</td>
          <td>${UI.badge(item.reason || 'allowed', item.reason ? 'orange' : 'green')}</td>
          <td>${escapeHtml(item.time || '-')}</td>
        </tr>
      `).join('');
    } catch (err) {
      dnsRows = '<tr><td colspan="3">Unable to load DNS activity.</td></tr>';
    }

    const profileOptions = this.profiles.map(p => `
      <option value="${escapeHtml(p.name)}" ${p.name === d.profile ? 'selected' : ''}>${escapeHtml(p.name)}</option>
    `).join('');

    const root = document.getElementById('modal-root') || document.body.appendChild(document.createElement('div'));
    root.id = 'modal-root';

    root.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal">
          <div class="modal-head">
            <h3>Edit Device</h3>
          </div>
          <div class="modal-body">
            <div class="edit-device-head">
              <div class="edit-device-icon">${deviceIcon(d)}</div>
              <div>
                <strong>${escapeHtml(d.alias || d.hostname || 'Unknown Device')}</strong>
                <span>${escapeHtml(d.ip || 'No IP')} · ${escapeHtml(d.mac)}</span>
              </div>
            </div>

            <div class="device-detail-grid">
              <div><span>IP Address</span><strong>${escapeHtml(d.ip || '-')}</strong></div>
              <div><span>MAC</span><strong>${escapeHtml(d.mac || '-')}</strong></div>
              <div><span>Status</span><strong>${escapeHtml(d.status || 'unknown')}</strong></div>
              <div><span>Profile</span><strong>${escapeHtml(d.profile || 'default')}</strong></div>
              <div><span>Internet</span><strong>${escapeHtml(d.policy_internet || '-')}</strong></div>
              <div><span>QoS</span><strong>${escapeHtml(d.qos_label || 'QoS off')}</strong></div>
              <div><span>QoS Detail</span><strong>${escapeHtml(d.qos_queue_label || '-')}</strong></div>
            </div>

            <div class="device-dns-panel">
              <div class="mini-panel-title">Recent DNS Activity</div>
              <table class="table compact-table">
                <thead><tr><th>Domain</th><th>Status</th><th>Time</th></tr></thead>
                <tbody>${dnsRows || '<tr><td colspan="3">No DNS activity yet.</td></tr>'}</tbody>
              </table>
            </div>

            <div class="form-stack">
              <label>Alias</label>
              <input id="edit-alias" value="${escapeHtml(d.alias || '')}" placeholder="Friendly name">

              <label>Profile</label>
              <select id="edit-profile">${profileOptions}</select>

              <label>Reserved IP</label>
              <input id="edit-reserved-ip" value="${escapeHtml((DeviceActions.leases.find(l => l.mac === d.mac) || {}).ip || d.ip || '')}" placeholder="192.168.10.150">

              <label>Notes</label>
              <textarea id="edit-notes" placeholder="Device notes">${escapeHtml(d.notes || '')}</textarea>
            </div>
          </div>
          <div class="modal-actions">
            <button class="soft-button" onclick="DeviceActions.closeModal()">Cancel</button>
            <button class="primary-button" onclick="DeviceActions.save('${escapeHtml(d.mac)}')">Save Changes</button>
          </div>
        </div>
      </div>
    `;
  },

  closeModal() {
    const root = document.getElementById('modal-root');
    if (root) root.innerHTML = '';
  },

  async save(mac) {
    const alias = document.getElementById('edit-alias').value.trim();
    const profile = document.getElementById('edit-profile').value;
    const reservedIp = document.getElementById('edit-reserved-ip').value.trim();
    const notes = document.getElementById('edit-notes').value.trim();

    await NinjakuAPI.post('/devices/' + encodeURIComponent(mac) + '/alias', { alias });
    await NinjakuAPI.post('/devices/' + encodeURIComponent(mac) + '/profile', { profile });
    await NinjakuAPI.post('/devices/' + encodeURIComponent(mac) + '/notes', { notes });

    if (reservedIp) {
      await NinjakuAPI.post('/leases', { mac, ip: reservedIp, hostname: alias || mac.replaceAll(':', '-') });
    }

    this.closeModal();
    UI.toast('success', 'Device updated', 'Alias, profile and notes were saved.');
    await Ninjaku.navigate('devices');
  }
};
