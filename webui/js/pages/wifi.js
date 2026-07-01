window.Pages = window.Pages || {};

function fmtSeconds(s) {
  s = Number(s || 0);
  if (s < 60) return s + 's';
  const m = Math.floor(s / 60);
  if (m < 60) return m + 'm ' + (s % 60) + 's';
  const h = Math.floor(m / 60);
  return h + 'h ' + (m % 60) + 'm';
}

Pages.wifi = {
  title: 'Wireless',
  subtitle: 'WiFi access point, stations and client monitoring.',

  async render() {
    const [wifi, stations] = await Promise.all([
      NinjakuAPI.get('/wifi'),
      NinjakuAPI.get('/wifi/stations')
    ]);

    const c = wifi.config || {};
    const r = wifi.runtime || {};
    const stationRows = (stations.stations || []).map(st => `
      <tr>
        <td><strong>${escapeHtml(st.mac || '-')}</strong></td>
        <td>${UI.badge((st.signal || 0) > -65 ? 'Good' : 'Weak', (st.signal || 0) > -65 ? 'green' : 'orange')} ${escapeHtml(String(st.signal || '-'))} dBm</td>
        <td>${escapeHtml(st.rx_bitrate || '-')}</td>
        <td>${escapeHtml(st.tx_bitrate || '-')}</td>
        <td>${fmtSeconds(st.connected || 0)}</td>
        <td>${st.authorized ? UI.badge('authorized', 'green') : UI.badge('blocked', 'red')}</td>
      </tr>
    `).join('');

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '📶', color: r.hostapd_active ? 'green' : 'orange', label: 'Wireless AP', value: r.hostapd_active ? 'Running' : 'Stopped', sub: c.interface || 'wlan0' })}
        ${UI.statCard({ icon: '▣', color: 'blue', label: 'SSID', value: c.ssid || '-', sub: 'channel ' + (c.channel || '-') })}
        ${UI.statCard({ icon: '🌐', color: 'purple', label: 'Address', value: c.ip || '-', sub: c.country || 'ID' })}
        ${UI.statCard({ icon: '👥', color: (stations.count || 0) ? 'green' : 'orange', label: 'Clients', value: stations.count || 0, sub: 'connected stations' })}
      </section>

      ${UI.panel('Wireless Configuration', `
        <div class="form-grid wg-server-grid">
          <div><label>Interface</label><input id="wifi-interface" value="${escapeHtml(c.interface || 'wlan0')}"></div>
          <div><label>SSID</label><input id="wifi-ssid" value="${escapeHtml(c.ssid || 'Ninjaku')}"></div>
          <div><label>Password</label><input id="wifi-password" type="password" placeholder="Leave blank to keep current"></div>
          <div><label>Country</label><input id="wifi-country" value="${escapeHtml(c.country || 'ID')}"></div>
          <div><label>Channel</label><input id="wifi-channel" value="${escapeHtml(c.channel || '6')}"></div>
          <div><label>AP IP</label><input id="wifi-ip" value="${escapeHtml(c.ip || '192.168.50.1/24')}"></div>
        </div>
      `, `
        <button class="primary-button" onclick="WifiActions.save()">Save</button>
        ${r.hostapd_active
          ? '<button class="danger-button" onclick="WifiActions.stop()">Stop AP</button><button class="soft-button" onclick="WifiActions.restart()">Restart AP</button>'
          : '<button class="primary-button" onclick="WifiActions.start()">Start AP</button>'}
      `)}

      ${UI.panel('Connected WiFi Clients', `
        <table class="table">
          <thead><tr><th>MAC</th><th>Signal</th><th>RX</th><th>TX</th><th>Connected</th><th>Status</th></tr></thead>
          <tbody>${stationRows || '<tr><td colspan="6">No WiFi clients connected.</td></tr>'}</tbody>
        </table>
      `)}

      ${UI.panel('Runtime', `
        <pre>${escapeHtml(r.interface || '')}</pre>
        <pre>${escapeHtml(r.iw || '')}</pre>
      `)}
    `;
  }
};

window.WifiActions = {
  async save() {
    const payload = {
      interface: document.getElementById('wifi-interface').value.trim(),
      ssid: document.getElementById('wifi-ssid').value.trim(),
      country: document.getElementById('wifi-country').value.trim(),
      channel: document.getElementById('wifi-channel').value.trim(),
      ip: document.getElementById('wifi-ip').value.trim()
    };

    const pwd = document.getElementById('wifi-password').value.trim();
    if (pwd) payload.password = pwd;

    await NinjakuAPI.post('/wifi/config', payload);
    UI.toast('success', 'Wireless saved', 'WiFi configuration was saved.');
    await Ninjaku.navigate('wifi');
  },

  async start() {
    UI.busy.show('Starting WiFi AP...', 'Applying hostapd and interface configuration.');
    const r = await NinjakuAPI.post('/wifi/start');
    UI.busy.hide();
    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'WiFi AP started' : 'WiFi AP failed', r.stderr || '');
    await Ninjaku.navigate('wifi');
  },

  async stop() {
    const r = await NinjakuAPI.post('/wifi/stop');
    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'WiFi AP stopped' : 'Stop failed', r.stderr || '');
    await Ninjaku.navigate('wifi');
  },

  async restart() {
    UI.busy.show('Restarting WiFi AP...', 'Clients may reconnect after a few seconds.');
    const r = await NinjakuAPI.post('/wifi/restart');
    UI.busy.hide();
    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'WiFi AP restarted' : 'Restart failed', r.stderr || '');
    await Ninjaku.navigate('wifi');
  }
};
