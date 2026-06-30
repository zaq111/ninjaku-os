window.Pages = window.Pages || {};

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
    const [data, profilesData] = await Promise.all([
      NinjakuAPI.get('/devices'),
      NinjakuAPI.get('/profiles')
    ]);

    DeviceActions.devices = data.devices || [];
    DeviceActions.profiles = profilesData.profiles || [];

    const devices = DeviceActions.devices;
    const online = devices.filter(d => d.status === 'online').length;
    const offline = devices.filter(d => d.status === 'offline').length;

    const rows = devices.map(d => `
      <tr>
        <td>${deviceIcon(d)} <strong>${escapeHtml(d.alias || d.hostname || 'Unknown')}</strong></td>
        <td>${escapeHtml(d.ip)}</td>
        <td>${escapeHtml(d.mac)}</td>
        <td>${UI.badge(d.profile || 'default', 'blue')}</td>
        <td>${UI.badge(d.status || 'unknown', statusColor(d.status))}</td>
        <td>${escapeHtml(d.policy_bandwidth || '')}</td>
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
          <thead><tr><th>Device</th><th>IP Address</th><th>MAC</th><th>Profile</th><th>Status</th><th>Bandwidth</th><th>Action</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="7">No devices found.</td></tr>'}</tbody>
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

  edit(mac) {
    const d = this.devices.find(x => x.mac === mac);
    if (!d) return UI.toast('error', 'Device not found', mac);

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

            <div class="form-stack">
              <label>Alias</label>
              <input id="edit-alias" value="${escapeHtml(d.alias || '')}" placeholder="Friendly name">

              <label>Profile</label>
              <select id="edit-profile">${profileOptions}</select>

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
    const notes = document.getElementById('edit-notes').value.trim();

    await NinjakuAPI.post('/devices/' + encodeURIComponent(mac) + '/alias', { alias });
    await NinjakuAPI.post('/devices/' + encodeURIComponent(mac) + '/profile', { profile });
    await NinjakuAPI.post('/devices/' + encodeURIComponent(mac) + '/notes', { notes });

    this.closeModal();
    UI.toast('success', 'Device updated', 'Alias, profile and notes were saved.');
    await Ninjaku.navigate('devices');
  }
};
