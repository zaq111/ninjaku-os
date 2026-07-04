window.Pages = window.Pages || {};

function policyQosDetail(p) {
  if (!p.qos_enabled) return '<span class="muted">disabled</span>';

  const mode = p.qos_mode || 'priority';

  if (mode === 'limiter') {
    const down = String(p.qos_download || '0').replace(/mbit|mbps/gi, '') || '0';
    const up = String(p.qos_upload || '0').replace(/mbit|mbps/gi, '') || '0';
    return `${UI.badge('Limiter', 'orange')} ${escapeHtml(down)}/${escapeHtml(up)} Mbps · ${escapeHtml(p.qos_priority || 'normal')}`;
  }

  return `${UI.badge('CAKE Marking', 'blue')} <span class="muted">global application/protocol rules</span>`;
}

Pages.policy = {
  title: 'Policy',
  subtitle: 'Profile-based internet, DNS, QoS and device policy.',

  async render() {
    const [policyData, devicesData] = await Promise.all([
      NinjakuAPI.get('/policy'),
      NinjakuAPI.get('/devices')
    ]);

    PolicyActions.policies = policyData.policies || [];
    PolicyActions.devices = devicesData.devices || [];

    const rows = PolicyActions.policies.map(p => {
      const devices = PolicyActions.devices.filter(d => (d.profile || 'default') === p.profile);
      const profileOptions = PolicyActions.policies.map(x =>
        `<option value="${escapeHtml(x.profile)}" ${x.profile === p.profile ? 'selected' : ''}>${escapeHtml(x.profile)}</option>`
      ).join('');

      const deviceRows = devices.map(d => `
        <tr class="policy-device-row">
          <td></td>
          <td colspan="2"><strong>${escapeHtml(d.alias || d.hostname || 'Unknown')}</strong></td>
          <td>${escapeHtml(d.ip || '-')}</td>
          <td>${escapeHtml(d.mac || '-')}</td>
          <td>${UI.badge(d.status || 'unknown', statusColor(d.status))}</td>
          <td>
            <select class="mini-select" onchange="PolicyActions.moveDevice('${escapeHtml(d.mac)}', this.value)">
              ${profileOptions}
            </select>
          </td>
          <td></td>
        </tr>
      `).join('');

      return `
        <tr class="policy-main-row" onclick="PolicyActions.toggle('${escapeHtml(p.profile)}')">
          <td><button class="row-toggle" id="toggle-${escapeHtml(p.profile)}">+</button> <strong>${escapeHtml(p.profile)}</strong> <span class="muted">(${devices.length})</span></td>
          <td>${UI.badge(p.internet, p.internet === 'allow' ? 'green' : 'red')}</td>
          <td>${escapeHtml(p.dns_filter)}</td>
          <td>${escapeHtml(p.schedule)}</td>
          <td>${UI.badge(p.qos_enabled ? (p.qos_mode || 'priority') : 'off', p.qos_enabled ? 'green' : 'orange')}</td>
          <td colspan="2">${policyQosDetail(p)}</td>
          <td><button class="soft-button" onclick="event.stopPropagation(); PolicyActions.edit('${escapeHtml(p.profile)}')">Edit</button></td>
        </tr>
        <tbody id="policy-devices-${escapeHtml(p.profile)}" class="policy-devices hidden">
          ${deviceRows || `<tr class="policy-device-row"><td></td><td colspan="7" class="muted">No devices in this profile.</td></tr>`}
        </tbody>
      `;
    }).join('');

    return UI.panel('Policies', `
      <table class="table policy-table">
        <thead>
          <tr>
            <th>Profile</th><th>Internet</th><th>DNS</th><th>Schedule</th>
            <th>QoS</th><th colspan="2">QoS Detail</th><th>Action</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `, `<button class="primary-button" onclick="PolicyActions.apply()">Apply Policy</button>`);
  }
};

window.PolicyActions = {
  policies: [],
  devices: [],

  toggle(profile) {
    const body = document.getElementById('policy-devices-' + profile);
    const btn = document.getElementById('toggle-' + profile);
    if (!body) return;

    body.classList.toggle('hidden');
    if (btn) btn.textContent = body.classList.contains('hidden') ? '+' : '−';
  },

  async moveDevice(mac, profile) {
    await NinjakuAPI.post('/devices/' + encodeURIComponent(mac) + '/profile', { profile });
    UI.toast('success', 'Device moved', 'Device profile was updated.');
    await Ninjaku.navigate('policy');
  },

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
                <input type="checkbox" id="policy-qos-enabled" ${p.qos_enabled ? 'checked' : ''} onchange="PolicyActions.toggleQosFields()">
                Enable QoS priority for this policy
              </label>

              <label>QoS Mode</label>
              <select id="policy-qos-mode" ${p.qos_enabled ? '' : 'disabled'} onchange="PolicyActions.toggleQosFields()">
                <option value="priority" ${(p.qos_mode || 'priority') === 'priority' ? 'selected' : ''}>Priority / Marking</option>
                <option value="limiter" ${(p.qos_mode || 'priority') === 'limiter' ? 'selected' : ''}>Limiter</option>
              </select>
              <small id="policy-qos-mode-help" class="muted"></small>

              <div id="policy-limiter-fields">
                <label>Download Limit (Mbps)</label>
                <input id="policy-qos-download" value="${escapeHtml(p.qos_download || '')}" placeholder="10">

                <label>Upload Limit (Mbps)</label>
                <input id="policy-qos-upload" value="${escapeHtml(p.qos_upload || '')}" placeholder="2">

                <label>Limiter Priority</label>
                <select id="policy-qos-priority">
                  <option value="low" ${p.qos_priority === 'low' ? 'selected' : ''}>low</option>
                  <option value="normal" ${p.qos_priority === 'normal' ? 'selected' : ''}>normal</option>
                  <option value="high" ${p.qos_priority === 'high' ? 'selected' : ''}>high</option>
                </select>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button class="soft-button" onclick="PolicyActions.close()">Cancel</button>
            <button class="primary-button" onclick="PolicyActions.save('${escapeHtml(p.profile)}')">Save Policy</button>
          </div>
        </div>
      </div>
    `;

    setTimeout(() => PolicyActions.toggleQosFields(), 0);
  },

  toggleQosFields() {
    const enabled = document.getElementById('policy-qos-enabled').checked;
    const mode = document.getElementById('policy-qos-mode')?.value || 'priority';

    const modeEl = document.getElementById('policy-qos-mode');
    const limiterBox = document.getElementById('policy-limiter-fields');
    const downEl = document.getElementById('policy-qos-download');
    const upEl = document.getElementById('policy-qos-upload');
    const prioEl = document.getElementById('policy-qos-priority');
    const helpEl = document.getElementById('policy-qos-mode-help');

    if (modeEl) modeEl.disabled = !enabled;

    if (!enabled) {
      if (limiterBox) limiterBox.style.display = 'none';
      if (downEl) downEl.disabled = true;
      if (upEl) upEl.disabled = true;
      if (prioEl) prioEl.disabled = true;
      if (helpEl) helpEl.textContent = 'QoS disabled for this profile.';
      return;
    }

    if (mode === 'limiter') {
      if (limiterBox) limiterBox.style.display = '';
      if (downEl) downEl.disabled = false;
      if (upEl) upEl.disabled = false;
      if (prioEl) prioEl.disabled = false;
      if (helpEl) helpEl.textContent = 'Limiter mode: enforces maximum bandwidth. Priority affects tc limiter scheduling: high gets lower filter priority number, low gets lower scheduling preference.';
    } else {
      if (limiterBox) limiterBox.style.display = 'none';
      if (downEl) downEl.disabled = true;
      if (upEl) upEl.disabled = true;
      if (prioEl) prioEl.disabled = true;
      if (helpEl) helpEl.textContent = 'Marking mode: uses global CAKE/application marking. No per-device limit or priority is applied.';
    }
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
      qos_mode: document.getElementById('policy-qos-mode').value,
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
    UI.toast('success', 'Policy applied', 'Firewall and QoS policy were refreshed.');
    await Ninjaku.navigate('policy');
  }
};
