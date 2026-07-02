window.Pages = window.Pages || {};


function cakeMapping(mode) {
  const maps = {
    besteffort: [
      ['Best Effort','CS0-CS7, AFxx, EF','Semua trafik diperlakukan sama (single queue).']
    ],
    diffserv3: [
      ['High / Latency','CS5, EF, CS6, CS7','Gaming, SSH, DNS, VoIP, trafik sensitif latency.'],
      ['Normal','CS0, AFxx','Web, aplikasi umum, trafik normal.'],
      ['Low / Bulk','CS1','Background, backup, torrent, trafik rendah prioritas.']
    ],
    diffserv4: [
      ['Voice','CS5, EF, CS6, CS7','VoIP, gaming, DNS, SSH, trafik latency-sensitive.'],
      ['Video','AF41, AF42, AF43','Streaming/video yang butuh throughput stabil.'],
      ['Best Effort','CS0','Trafik normal seperti browsing dan aplikasi umum.'],
      ['Bulk','CS1','Download latar belakang, torrent, update.']
    ],
    diffserv8: [
      ['Network Control','CS7, CS6','Routing protocol, network control.'],
      ['Voice','EF, CS5','VoIP, gaming, SSH, DNS.'],
      ['Video','AF41, AF42, AF43','Streaming dan video conference.'],
      ['Excellent Effort','AF31, AF32, AF33','Aplikasi penting non real-time.'],
      ['Best Effort','CS0','Browsing, aplikasi umum.'],
      ['Low Latency','CS4','Interactive applications.'],
      ['Background','CS2, CS3','Background service.'],
      ['Bulk','CS1','Download, torrent, backup.']
    ]
};
  return maps[mode] || maps.diffserv4;
}

function cakeMappingHtml(mode) {
  const list = cakeMapping(mode);
  const rows = list.map((r, idx) => `
    <tr>
      <td><strong>#${idx + 1}</strong></td>
      <td><strong>${escapeHtml(r[0])}</strong></td>
      <td>${escapeHtml(r[1])}</td>
      <td>${escapeHtml(r[2])}</td>
    </tr>
  `).join('');

  return `
    <div class="cake-map">
      <div class="muted" style="margin-bottom:8px">Order shown from highest priority to lowest priority.</div>
      <table class="table">
        <thead><tr><th>Priority</th><th>CAKE Queue</th><th>DSCP Values</th><th>Meaning</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}


function qosMbps(v) {
  return String(v || '').replace(/mbit|mbps|m/gi, '').trim();
}

Pages.qos = {
  title: 'QoS',
  subtitle: 'Global CAKE shaping, profile priority and limiter runtime.',

  async render() {
    const data = await NinjakuAPI.get('/qos');
    const c = data.config || {};
    const priorityRules = data.profile_rules || [];
    const limitRules = data.profile_limit_rules || [];

    const priorityRows = priorityRules.map(r => `
      <tr>
        <td><strong>${escapeHtml(r[2])}</strong></td>
        <td>${escapeHtml(r[0])}</td>
        <td>${UI.badge(r[1], r[1] === 'cs5' ? 'green' : 'orange')}</td>
      </tr>
    `).join('');

    const limitRows = limitRules.map(r => `
      <tr>
        <td><strong>${escapeHtml(r.profile || '-')}</strong></td>
        <td>${escapeHtml(r.ip || '-')}</td>
        <td>${escapeHtml(qosMbps(r.download) || 'unlimited')} Mbps</td>
        <td>${escapeHtml(qosMbps(r.upload) || 'unlimited')} Mbps</td>
      </tr>
    `).join('');

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '⚡', color: data.enabled === 'true' ? 'green' : 'orange', label: 'QoS', value: data.enabled === 'true' ? 'Enabled' : 'Disabled', sub: 'CAKE + Profile Rules' })}
        ${UI.statCard({ icon: '↑', color: 'blue', label: 'Upload', value: qosMbps(c.upload || '-') + ' Mbps', sub: c.wan || 'WAN' })}
        ${UI.statCard({ icon: '↓', color: 'purple', label: 'Download', value: qosMbps(c.download || '-') + ' Mbps', sub: c.ifb || 'IFB' })}
        ${UI.statCard({ icon: '✓', color: data.wan_exists ? 'green' : 'red', label: 'WAN', value: c.wan || '-', sub: data.wan_exists ? 'available' : 'missing' })}
      </section>

      ${UI.panel('QoS Engine', `
        <div class="form-grid qos-form">
          <div><label>WAN Interface</label><input id="qos-wan" value="${escapeHtml(c.wan || 'eth0')}"></div>
          <div><label>Download Speed (Mbps)</label><input id="qos-download" value="${escapeHtml(qosMbps(c.download || '90'))}"></div>
          <div><label>Upload Speed (Mbps)</label><input id="qos-upload" value="${escapeHtml(qosMbps(c.upload || '90'))}"></div>

          <div><label>CAKE Mode</label>
            <select id="qos-diffserv" onchange="QosActions.updateCakeMap()">
              <option value="besteffort" ${c.diffserv === 'besteffort' ? 'selected' : ''}>Best Effort</option>
              <option value="diffserv3" ${c.diffserv === 'diffserv3' ? 'selected' : ''}>Diffserv 3</option>
              <option value="diffserv4" ${c.diffserv === 'diffserv4' ? 'selected' : ''}>Diffserv 4</option>
              <option value="diffserv8" ${c.diffserv === 'diffserv8' ? 'selected' : ''}>Diffserv 8</option>
            </select>
          </div>

          <div><label>Processing Strategy</label>
            <select id="qos-strategy">
              <option value="balanced" ${c.strategy === 'balanced' ? 'selected' : ''}>Balanced</option>
              <option value="priority_first" ${c.strategy === 'priority_first' ? 'selected' : ''}>Priority First</option>
              <option value="limiter_first" ${c.strategy === 'limiter_first' ? 'selected' : ''}>Limiter First</option>
            </select>
          </div>
        </div>

        <div style="margin-top:16px">
          <h4>CAKE Queue Mapping Preview</h4>
          <div id="cake-map-preview">${cakeMappingHtml(c.diffserv || 'diffserv4')}</div>
        </div>

        <details style="margin-top:16px">
          <summary><strong>Advanced CAKE Settings</strong></summary>
          <div class="form-grid qos-form" style="margin-top:14px">
            <div><label>Overhead</label><input id="qos-overhead" value="${escapeHtml(c.overhead || '0')}"></div>
            <div><label>MPU</label><input id="qos-mpu" value="${escapeHtml(c.mpu || '0')}"></div>
            <div><label>RTT</label><input id="qos-rtt" value="${escapeHtml(c.rtt || '')}" placeholder="100ms"></div>
            <div><label>High Priority DSCP</label><input id="qos-map-high" value="${escapeHtml(c['map.high'] || 'cs5')}"></div>
            <div><label>Normal Priority DSCP</label><input id="qos-map-normal" value="${escapeHtml(c['map.normal'] || 'cs0')}"></div>
            <div><label>Low Priority DSCP</label><input id="qos-map-low" value="${escapeHtml(c['map.low'] || 'cs1')}"></div>
          </div>

          <div class="qos-checks">
            <label><input type="checkbox" id="qos-nat" ${c.nat === 'true' ? 'checked' : ''}> NAT aware</label>
            <label><input type="checkbox" id="qos-ack" ${c.ack_filter === 'true' ? 'checked' : ''}> ACK filter</label>
            <label><input type="checkbox" id="qos-wash" ${c.wash === 'true' ? 'checked' : ''}> Wash DSCP</label>
            <label><input type="checkbox" id="qos-split" ${c.split_gso === 'true' ? 'checked' : ''}> Split GSO</label>
          </div>
        </details>
      `, `
        <button class="primary-button" onclick="QosActions.saveApply()">Save & Apply</button>
        <button class="danger-button" onclick="QosActions.disable()">Disable QoS</button>
      `)}

      ${UI.panel('Active Profile Limiters', `
        <table class="table">
          <thead><tr><th>Profile</th><th>Client IP</th><th>Download</th><th>Upload</th></tr></thead>
          <tbody>${limitRows || '<tr><td colspan="4">No limiter rules active.</td></tr>'}</tbody>
        </table>
      `)}

      ${UI.panel('Active Priority Marking', `
        <table class="table">
          <thead><tr><th>Profile</th><th>Client IP</th><th>DSCP</th></tr></thead>
          <tbody>${priorityRows || '<tr><td colspan="3">No priority marking rules active.</td></tr>'}</tbody>
        </table>
      `)}

      ${UI.panel('Diagnostics', `
        <details>
          <summary><strong>WAN qdisc</strong></summary>
          <pre>${escapeHtml(data.wan_qdisc || 'No qdisc data')}</pre>
        </details>
        <details>
          <summary><strong>IFB Download qdisc</strong></summary>
          <pre>${escapeHtml(data.ifb_qdisc || 'No IFB qdisc data')}</pre>
        </details>
        <details>
          <summary><strong>WiFi Limiter qdisc</strong></summary>
          <pre>${escapeHtml(data.wifi_limit_qdisc || 'No WiFi limiter qdisc')}</pre>
          <pre>${escapeHtml(data.wifi_ifb_qdisc || 'No WiFi IFB qdisc')}</pre>
        </details>
      `)}
    `;
  }
};

window.QosActions = {
  updateCakeMap() {
    const mode = document.getElementById('qos-diffserv')?.value || 'diffserv4';
    const box = document.getElementById('cake-map-preview');
    if (box) box.innerHTML = cakeMappingHtml(mode);
  },

  readForm() {
    return {
      wan: document.getElementById('qos-wan').value.trim(),
      download: document.getElementById('qos-download').value.trim(),
      upload: document.getElementById('qos-upload').value.trim(),
      diffserv: document.getElementById('qos-diffserv').value,
      strategy: document.getElementById('qos-strategy').value,
      overhead: document.getElementById('qos-overhead').value.trim() || '0',
      mpu: document.getElementById('qos-mpu').value.trim() || '0',
      rtt: document.getElementById('qos-rtt').value.trim(),
      "map.high": document.getElementById('qos-map-high').value.trim() || 'cs5',
      "map.normal": document.getElementById('qos-map-normal').value.trim() || 'cs0',
      "map.low": document.getElementById('qos-map-low').value.trim() || 'cs1',
      nat: document.getElementById('qos-nat').checked ? 'true' : 'false',
      ack_filter: document.getElementById('qos-ack').checked ? 'true' : 'false',
      wash: document.getElementById('qos-wash').checked ? 'true' : 'false',
      split_gso: document.getElementById('qos-split').checked ? 'true' : 'false'
    };
  },

  async saveApply() {
    UI.busy.show('Applying QoS...', 'Updating CAKE, DSCP marking and profile limiters.');
    await NinjakuAPI.post('/qos', this.readForm());
    const r = await NinjakuAPI.post('/qos/apply');
    UI.busy.hide();

    UI.toast(r.ok ? 'success' : 'error', r.ok ? 'QoS applied' : 'QoS failed', r.error || '');
    await Ninjaku.navigate('qos');
  },

  async disable() {
    const ok = await UI.confirm({
      title: 'Disable QoS?',
      message: 'Traffic shaping will be removed from WAN, IFB and WiFi profile limiters.',
      confirmText: 'Disable',
      danger: true
    });

    if (!ok) return;

    UI.busy.show('Disabling QoS...', 'Removing traffic shaping rules.');
    await NinjakuAPI.post('/qos/disable');
    UI.busy.hide();

    UI.toast('success', 'QoS disabled', 'Traffic shaping was removed.');
    await Ninjaku.navigate('qos');
  }
};
