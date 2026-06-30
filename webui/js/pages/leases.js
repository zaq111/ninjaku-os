window.Pages = window.Pages || {};

Pages.leases = {
  title: 'Static Leases',
  subtitle: 'Reserved DHCP addresses for known devices.',

  async render() {
    const data = await NinjakuAPI.get('/leases');
    const leases = data.leases || [];

    const rows = leases.map(l => `
      <tr>
        <td><strong>${escapeHtml(l.ip)}</strong></td>
        <td>${escapeHtml(l.mac)}</td>
        <td>${escapeHtml(l.hostname)}</td>
        <td>${UI.badge(l.enabled ? 'enabled' : 'disabled', l.enabled ? 'green' : 'orange')}</td>
        <td>
          <button class="danger-button" onclick="LeaseActions.remove('${escapeHtml(l.mac)}')">Delete</button>
        </td>
      </tr>
    `).join('');

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '⇄', color: 'blue', label: 'Static Leases', value: leases.length, sub: 'reserved clients' })}
        ${UI.statCard({ icon: '✓', color: 'green', label: 'Enabled', value: leases.filter(l => l.enabled).length, sub: 'active reservations' })}
        ${UI.statCard({ icon: '◷', color: 'purple', label: 'Backend', value: 'dnsmasq', sub: 'DHCP backend' })}
        ${UI.statCard({ icon: '▣', color: 'orange', label: 'Config', value: 'Generated', sub: 'automatic file' })}
      </section>

      ${UI.panel('Add Static Lease', `
        <div class="form-grid">
          <input id="lease-mac" placeholder="MAC address, e.g. aa:bb:cc:dd:ee:ff">
          <input id="lease-ip" placeholder="IP address, e.g. 192.168.10.150">
          <input id="lease-hostname" placeholder="Hostname (optional)">
          <button class="primary-button" onclick="LeaseActions.add()">Add Lease</button>
        </div>
      `)}

      ${UI.panel('Reserved Addresses', `
        <table class="table">
          <thead><tr><th>IP Address</th><th>MAC</th><th>Hostname</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="5">No static leases configured.</td></tr>'}</tbody>
        </table>
      `, `<button class="soft-button" onclick="LeaseActions.apply()">Apply</button>`)}
    `;
  }
};

window.LeaseActions = {
  async add() {
    const mac = document.getElementById('lease-mac').value.trim();
    const ip = document.getElementById('lease-ip').value.trim();
    const hostname = document.getElementById('lease-hostname').value.trim();

    if (!mac || !ip) {
      alert('MAC and IP are required.');
      return;
    }

    await NinjakuAPI.post('/leases', { mac, ip, hostname });
    await Ninjaku.navigate('leases');
  },

  async remove(mac) {
    if (!confirm('Delete static lease for ' + mac + '?')) return;
    await NinjakuAPI.delete('/leases/' + encodeURIComponent(mac));
    await Ninjaku.navigate('leases');
  },

  async apply() {
    await NinjakuAPI.post('/leases/apply');
    await Ninjaku.navigate('leases');
  }
};
