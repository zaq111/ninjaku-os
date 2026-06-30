window.Pages = window.Pages || {};

Pages.dns_filter = {
  title: 'DNS Filter',
  subtitle: 'Lightweight ad and domain blocking powered by dnsmasq.',

  async render() {
    const data = await NinjakuAPI.get('/dns-filter');
    const domains = data.domains || [];
    const enabled = domains.filter(d => d.enabled).length;

    const rows = domains.map(d => `
      <tr>
        <td><strong>${escapeHtml(d.domain)}</strong></td>
        <td>${escapeHtml(d.list_name)}</td>
        <td>${UI.badge(d.enabled ? 'enabled' : 'disabled', d.enabled ? 'green' : 'orange')}</td>
        <td>
          <button class="danger-button" onclick="DnsFilterActions.remove('${escapeHtml(d.domain)}')">Delete</button>
        </td>
      </tr>
    `).join('');

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '🛡', color: 'blue', label: 'DNS Filter', value: 'Enabled', sub: 'dnsmasq backend' })}
        ${UI.statCard({ icon: '▣', color: 'purple', label: 'Blocked Domains', value: domains.length, sub: 'total entries' })}
        ${UI.statCard({ icon: '✓', color: 'green', label: 'Active Rules', value: enabled, sub: 'enabled domains' })}
        ${UI.statCard({ icon: '⇄', color: 'orange', label: 'Backend', value: 'dnsmasq', sub: 'lightweight mode' })}
      </section>

      ${UI.panel('Add Blocked Domain', `
        <div class="form-grid">
          <input id="dns-domain" placeholder="Domain, e.g. ads.example.com">
          <button class="primary-button" onclick="DnsFilterActions.add()">Add Domain</button>
        </div>
      `)}

      ${UI.panel('Blocked Domains', `
        <table class="table">
          <thead><tr><th>Domain</th><th>List</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="4">No blocked domains configured.</td></tr>'}</tbody>
        </table>
      `, `<button class="soft-button" onclick="DnsFilterActions.apply()">Apply</button>`)}
    `;
  }
};

window.DnsFilterActions = {
  async add() {
    const domain = document.getElementById('dns-domain').value.trim();
    if (!domain) {
      alert('Domain is required.');
      return;
    }

    await NinjakuAPI.post('/dns-filter/domains', { domain });
    await Ninjaku.navigate('dns_filter');
  },

  async remove(domain) {
    if (!confirm('Delete blocked domain ' + domain + '?')) return;
    await NinjakuAPI.delete('/dns-filter/domains/' + encodeURIComponent(domain));
    await Ninjaku.navigate('dns_filter');
  },

  async apply() {
    await NinjakuAPI.post('/dns-filter/apply');
    await Ninjaku.navigate('dns_filter');
  }
};
