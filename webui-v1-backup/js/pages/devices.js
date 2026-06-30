window.Pages = window.Pages || {};

function deviceIcon(d) {
  const name = `${d.hostname || ''} ${d.alias || ''}`.toLowerCase();

  if (name.includes('android') || name.includes('iphone') || name.includes('samsung') || name.includes('phone')) return '📱';
  if (name.includes('tv') || name.includes('androidtv')) return '📺';
  if (name.includes('esp') || name.includes('iot')) return '💡';
  if (name.includes('printer')) return '🖨️';
  if (name.includes('desktop') || name.includes('pc')) return '🖥️';
  if (name.includes('laptop')) return '💻';

  return '🌐';
}

function deviceStatusClass(status) {
  if (status === 'online') return 'ok';
  if (status === 'offline') return 'fail';
  return 'warn';
}

Pages.devices = {
  title: 'Devices',
  subtitle: 'LAN clients, profiles and effective policy',

  async render() {
    const data = await NinjakuAPI.get('/devices');
    const devices = data.devices || [];

    const online = devices.filter(d => d.status === 'online').length;
    const offline = devices.filter(d => d.status === 'offline').length;
    const unknown = devices.length - online - offline;

    const cards = devices.map(d => `
      <div class="device-card">
        <div class="device-icon">${deviceIcon(d)}</div>
        <div class="device-main">
          <div class="device-title">${escapeHtml(d.alias || d.hostname || d.mac || 'Unknown Device')}</div>
          <div class="device-sub">${escapeHtml(d.ip || 'No IP')} · ${escapeHtml(d.mac || '')}</div>
          <div class="device-tags">
            <span class="badge ${deviceStatusClass(d.status)}">${escapeHtml(d.status || 'unknown')}</span>
            <span class="badge">${escapeHtml(d.profile || 'default')}</span>
            <span class="badge">${escapeHtml(d.policy_internet || 'allow')}</span>
            <span class="badge">${escapeHtml(d.policy_bandwidth || 'unlimited')}</span>
          </div>
        </div>
      </div>
    `).join('');

    const tableRows = devices.map(d => `
      <tr>
        <td>${escapeHtml(d.ip)}</td>
        <td>${escapeHtml(d.mac)}</td>
        <td class="${deviceStatusClass(d.status)}">${escapeHtml(d.status)}</td>
        <td>${escapeHtml(d.profile)}</td>
        <td>${escapeHtml(d.policy_internet)}</td>
        <td>${escapeHtml(d.policy_bandwidth)}</td>
      </tr>
    `).join('');

    return `
      <section class="grid cards">
        <div class="card"><span>Total Devices</span><strong>${devices.length}</strong><p>known clients</p></div>
        <div class="card"><span>Online</span><strong class="ok">${online}</strong><p>currently visible</p></div>
        <div class="card"><span>Offline</span><strong class="fail">${offline}</strong><p>last seen before</p></div>
        <div class="card"><span>Unknown</span><strong class="warn">${unknown}</strong><p>not classified</p></div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3>Device Cards</h3>
          <button onclick="DeviceActions.sync()">Sync</button>
        </div>
        <div class="device-grid">
          ${cards || '<div class="empty-state">No devices found. Connect a client to LAN and click Sync.</div>'}
        </div>
      </section>

      <section class="panel">
        <h3>Device Table</h3>
        <table>
          <thead><tr><th>IP</th><th>MAC</th><th>Status</th><th>Profile</th><th>Internet</th><th>Bandwidth</th></tr></thead>
          <tbody>${tableRows || '<tr><td colspan="6">No devices found.</td></tr>'}</tbody>
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
