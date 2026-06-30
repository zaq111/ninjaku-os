window.Pages = window.Pages || {};

Pages.devices = {
  title: 'Devices',
  subtitle: 'LAN clients, profiles and effective policy',

  async render() {
    const data = await NinjakuAPI.get('/devices');
    const rows = (data.devices || []).map(d => `
      <tr>
        <td>${escapeHtml(d.ip)}</td>
        <td>${escapeHtml(d.mac)}</td>
        <td>${escapeHtml(d.status)}</td>
        <td>${escapeHtml(d.profile)}</td>
        <td>${escapeHtml(d.policy_internet)}</td>
        <td>${escapeHtml(d.policy_bandwidth)}</td>
      </tr>
    `).join('');

    return `
      <section class="panel">
        <div class="panel-head">
          <h3>Devices (${data.count || 0})</h3>
          <button onclick="DeviceActions.sync()">Sync</button>
        </div>
        <table>
          <thead><tr><th>IP</th><th>MAC</th><th>Status</th><th>Profile</th><th>Internet</th><th>Bandwidth</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="6">No devices found.</td></tr>'}</tbody>
        </table>
      </section>
    `;
  }
};

window.DeviceActions = {
  async sync() {
    await NinjakuAPI.post('/devices/sync');
    await Ninjaku.navigate('devices');
  }
};
