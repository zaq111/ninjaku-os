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
    const data = await NinjakuAPI.get('/devices');
    const devices = data.devices || [];
    const online = devices.filter(d => d.status === 'online').length;
    const offline = devices.filter(d => d.status === 'offline').length;

    const rows = devices.map(d => `
      <tr>
        <td>${deviceIcon(d)} ${escapeHtml(d.alias || d.hostname || 'Unknown')}</td>
        <td>${escapeHtml(d.ip)}</td>
        <td>${escapeHtml(d.mac)}</td>
        <td>${UI.badge(d.profile || 'default', 'blue')}</td>
        <td>${UI.badge(d.status || 'unknown', statusColor(d.status))}</td>
        <td>${escapeHtml(d.policy_bandwidth || '')}</td>
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
          <thead><tr><th>Device</th><th>IP Address</th><th>MAC</th><th>Profile</th><th>Status</th><th>Bandwidth</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="6">No devices found.</td></tr>'}</tbody>
        </table>
      `, `<button class="primary-button" onclick="DeviceActions.sync()">Sync</button>`)}
    `;
  }
};

window.DeviceActions = {
  async sync() {
    await NinjakuAPI.post('/devices/sync');
    await Ninjaku.navigate('devices');
  }
};
