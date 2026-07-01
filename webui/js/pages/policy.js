window.Pages = window.Pages || {};

Pages.policy = {
  title: 'Policy',
  subtitle: 'Profile-based internet, DNS and QoS policy.',

  async render() {
    const data = await NinjakuAPI.get('/policy');
    PolicyActions.policies = data.policies || [];

    const rows = PolicyActions.policies.map(p => `
      <tr>
        <td><strong>${escapeHtml(p.profile)}</strong></td>
        <td>${UI.badge(p.internet, p.internet === 'allow' ? 'green' : 'red')}</td>
        <td>${escapeHtml(p.dns_filter)}</td>
        <td>${escapeHtml(p.schedule)}</td>
        <td>${UI.badge(p.qos_enabled ? 'enabled' : 'off', p.qos_enabled ? 'green' : 'orange')}</td>
        <td>${p.qos_enabled ? `↓ ${escapeHtml(p.qos_download || 'unlimited')} / ↑ ${escapeHtml(p.qos_upload || 'unlimited')}` : '<span class="muted">disabled</span>'}</td>
        <td>${p.qos_enabled ? escapeHtml(p.qos_priority || 'normal') : '<span class="muted">-</span>'}</td>
        <td><button class="soft-button" onclick="PolicyActions.edit('${escapeHtml(p.profile)}')">Edit</button></td>
      </tr>
    `).join('');

    return UI.panel('Policies', `
      <table class="table">
        <thead>
          <tr>
            <th>Profile</th><th>Internet</th><th>DNS</th><th>Schedule</th>
            <th>QoS</th><th>Shape</th><th>Priority</th><th>Action</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `, `<button class="primary-button" onclick="PolicyActions.apply()">Apply Policy</button>`);
  }
};

window.PolicyActions = {
  policies: [],

  edit(profile) {
    const p = this.policies.find(x => x.profile === profile);
    if (!p) return UI.toast('error', 'Policy not found', profile);

    let root = document.getElementById('modal-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'modal-root';
      document.body.appendChild(root);
    }

    root.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal">
          <div class="modal-head"><h3>Edit Policy: ${escapeHtml(p.profile)}</h3></div>
          <div class="modal-body">
            <div class="form-stack">
              <label>Internet</label>
              <select id="policy-internet">
                <option value="allow" ${p.internet === 'allow' ? 'selected' : ''}>allow</option>
                <option value="deny" ${p.internet === 'deny' ? 'selected' : ''}>deny</option>
              </select>

              <label>DNS</label>
              <select id="policy-dns">
                <option value="adguard" ${p.dns_filter === 'adguard' ? 'selected' : ''}>adguard</option>
                <option value="none" ${p.dns_filter === 'none' ? 'selected' : ''}>none</option>
                <option value="basic" ${p.dns_filter === 'basic' ? 'selected' : ''}>basic</option>
              </select>

              <label>Schedule</label>
              <input id="policy-schedule" value="${escapeHtml(p.schedule || 'always')}">

              <label>QoS</label>
              <label class="inline-check">
                <input type="checkbox" id="policy-qos-enabled" ${p.qos_enabled ? 'checked' : ''}>
                Enable QoS priority for this policy
              </label>

              <label>Download Shape</label>
              <input id="policy-qos-download" value="${escapeHtml(p.qos_download || '')}" placeholder="20mbit">

              <label>Upload Shape</label>
              <input id="policy-qos-upload" value="${escapeHtml(p.qos_upload || '')}" placeholder="5mbit">

              <label>QoS Priority</label>
              <select id="policy-qos-priority">
                <option value="low" ${p.qos_priority === 'low' ? 'selected' : ''}>low</option>
                <option value="normal" ${p.qos_priority === 'normal' ? 'selected' : ''}>normal</option>
                <option value="high" ${p.qos_priority === 'high' ? 'selected' : ''}>high</option>
              </select>
            </div>
          </div>
          <div class="modal-actions">
            <button class="soft-button" onclick="PolicyActions.close()">Cancel</button>
            <button class="primary-button" onclick="PolicyActions.save('${escapeHtml(p.profile)}')">Save Policy</button>
          </div>
        </div>
      </div>
    `;
  },

  close() {
    const root = document.getElementById('modal-root');
    if (root) root.innerHTML = '';
  },

  async save(profile) {
    await NinjakuAPI.post('/policy/' + encodeURIComponent(profile), {
      internet: document.getElementById('policy-internet').value,
      dns_filter: document.getElementById('policy-dns').value,
      schedule: document.getElementById('policy-schedule').value.trim(),
      qos_enabled: document.getElementById('policy-qos-enabled').checked,
      qos_download: document.getElementById('policy-qos-download').value.trim(),
      qos_upload: document.getElementById('policy-qos-upload').value.trim(),
      qos_priority: document.getElementById('policy-qos-priority').value
    });

    await NinjakuAPI.post('/qos/apply');
    this.close();
    UI.toast('success', 'Policy saved', 'Policy and QoS rules were applied.');
    await Ninjaku.navigate('policy');
  },

  async apply() {
    await NinjakuAPI.post('/policy/apply');
    await NinjakuAPI.post('/qos/apply');
    UI.toast('success', 'Policy applied', 'Firewall and QoS policy were refreshed.');
    await Ninjaku.navigate('policy');
  }
};
