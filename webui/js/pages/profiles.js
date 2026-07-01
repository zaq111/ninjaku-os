window.Pages = window.Pages || {};

Pages.profiles = {
  title: 'Profiles',
  subtitle: 'Profiles combine device identity, policy and QoS.',

  async render() {
    const data = await NinjakuAPI.get('/profiles');
    ProfileActions.profiles = data.profiles || [];

    const cards = ProfileActions.profiles.map(p => `
      <div class="profile-card">
        <div class="profile-top">
          <div class="card-icon icon-${p.is_system ? 'blue' : 'purple'}">${p.is_system ? '★' : '♢'}</div>
          <div>
            <small>${p.is_system ? 'System Profile' : 'Custom Profile'}</small>
            <strong>${escapeHtml(p.name)}</strong>
            <span>${escapeHtml(p.description || '-')}</span>
          </div>
        </div>

        <div class="profile-qos">
          ${UI.badge(p.qos_enabled ? 'QoS enabled' : 'QoS off', p.qos_enabled ? 'green' : 'orange')}
          <span>↓ ${escapeHtml(p.qos_download || 'unlimited')}</span>
          <span>↑ ${escapeHtml(p.qos_upload || 'unlimited')}</span>
          <span>${escapeHtml(p.qos_priority || 'normal')}</span>
        </div>

        <div class="pipe-actions">
          <button class="soft-button" onclick="ProfileActions.edit('${escapeHtml(p.name)}')">Edit Profile</button>
        </div>
      </div>
    `).join('');

    return `<section class="grid grid-3">${cards}</section>`;
  }
};

window.ProfileActions = {
  profiles: [],

  edit(name) {
    const p = this.profiles.find(x => x.name === name);
    if (!p) return UI.toast('error', 'Profile not found', name);

    let root = document.getElementById('modal-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'modal-root';
      document.body.appendChild(root);
    }

    root.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal">
          <div class="modal-head"><h3>Edit Profile: ${escapeHtml(p.name)}</h3></div>
          <div class="modal-body">
            <div class="form-stack">
              <label>Description</label>
              <input id="profile-description" value="${escapeHtml(p.description || '')}">

              <label>QoS</label>
              <label class="inline-check">
                <input type="checkbox" id="profile-qos-enabled" ${p.qos_enabled ? 'checked' : ''}>
                Enable QoS shaping for this profile
              </label>

              <label>Download Shape</label>
              <input id="profile-qos-download" value="${escapeHtml(p.qos_download || '')}" placeholder="20mbit or empty for unlimited">

              <label>Upload Shape</label>
              <input id="profile-qos-upload" value="${escapeHtml(p.qos_upload || '')}" placeholder="5mbit or empty for unlimited">

              <label>Priority</label>
              <select id="profile-qos-priority">
                <option value="low" ${p.qos_priority === 'low' ? 'selected' : ''}>low</option>
                <option value="normal" ${p.qos_priority === 'normal' ? 'selected' : ''}>normal</option>
                <option value="high" ${p.qos_priority === 'high' ? 'selected' : ''}>high</option>
              </select>
            </div>
          </div>
          <div class="modal-actions">
            <button class="soft-button" onclick="ProfileActions.close()">Cancel</button>
            <button class="primary-button" onclick="ProfileActions.save('${escapeHtml(p.name)}')">Save Profile</button>
          </div>
        </div>
      </div>
    `;
  },

  close() {
    const root = document.getElementById('modal-root');
    if (root) root.innerHTML = '';
  },

  async save(name) {
    const data = {
      description: document.getElementById('profile-description').value.trim(),
      qos_enabled: document.getElementById('profile-qos-enabled').checked,
      qos_download: document.getElementById('profile-qos-download').value.trim(),
      qos_upload: document.getElementById('profile-qos-upload').value.trim(),
      qos_priority: document.getElementById('profile-qos-priority').value
    };

    await NinjakuAPI.post('/profiles/' + encodeURIComponent(name), data);
    this.close();
    UI.toast('success', 'Profile saved', 'Profile QoS settings were updated.');
    await Ninjaku.navigate('profiles');
  }
};
