window.Pages = window.Pages || {};

Pages.qos = {
  title: 'QoS',
  subtitle: 'Ninjaku traffic shaping powered by CAKE and IFB.',

  async render() {
    const data = await NinjakuAPI.get('/qos');
    const c = data.config || {};

    return `
      <section class="grid grid-4" style="margin-bottom:18px">
        ${UI.statCard({ icon: '⚡', color: data.enabled === 'true' ? 'green' : 'orange', label: 'QoS', value: data.enabled === 'true' ? 'Enabled' : 'Disabled', sub: 'CAKE smart shaping' })}
        ${UI.statCard({ icon: '↑', color: 'blue', label: 'Upload Shape', value: c.upload || '-', sub: c.wan || 'WAN' })}
        ${UI.statCard({ icon: '↓', color: 'purple', label: 'Download Shape', value: c.download || '-', sub: c.ifb || 'IFB' })}
        ${UI.statCard({ icon: '✓', color: data.wan_exists ? 'green' : 'red', label: 'WAN', value: c.wan || '-', sub: data.wan_exists ? 'available' : 'missing' })}
      </section>

      ${UI.panel('QoS Tuning', `
        <div class="form-grid qos-form">
          <input id="qos-wan" value="${escapeHtml(c.wan || 'eth0')}" placeholder="WAN interface">
          <input id="qos-download" value="${escapeHtml(c.download || '90mbit')}" placeholder="Download, e.g. 90mbit">
          <input id="qos-upload" value="${escapeHtml(c.upload || '90mbit')}" placeholder="Upload, e.g. 20mbit">
          <select id="qos-diffserv">
            <option value="besteffort" ${c.diffserv === 'besteffort' ? 'selected' : ''}>besteffort</option>
            <option value="diffserv3" ${c.diffserv === 'diffserv3' ? 'selected' : ''}>diffserv3</option>
            <option value="diffserv4" ${c.diffserv === 'diffserv4' ? 'selected' : ''}>diffserv4</option>
            <option value="diffserv8" ${c.diffserv === 'diffserv8' ? 'selected' : ''}>diffserv8</option>
          </select>
          <input id="qos-overhead" value="${escapeHtml(c.overhead || '0')}" placeholder="Overhead">
          <input id="qos-mpu" value="${escapeHtml(c.mpu || '0')}" placeholder="MPU">
          <input id="qos-rtt" value="${escapeHtml(c.rtt || '')}" placeholder="RTT optional, e.g. 100ms">
        </div>

        <div class="qos-checks">
          <label><input type="checkbox" id="qos-nat" ${c.nat === 'true' ? 'checked' : ''}> NAT aware</label>
          <label><input type="checkbox" id="qos-ack" ${c.ack_filter === 'true' ? 'checked' : ''}> ACK filter</label>
          <label><input type="checkbox" id="qos-wash" ${c.wash === 'true' ? 'checked' : ''}> Wash DSCP</label>
          <label><input type="checkbox" id="qos-split" ${c.split_gso === 'true' ? 'checked' : ''}> Split GSO</label>
        </div>
      `, `
        <button class="primary-button" onclick="QosActions.saveApply()">Save & Apply</button>
        <button class="danger-button" onclick="QosActions.disable()">Disable QoS</button>
      `)}

      ${UI.panel('WAN qdisc', `<pre>${escapeHtml(data.wan_qdisc || 'No qdisc data')}</pre>`)}
      ${UI.panel('IFB Download qdisc', `<pre>${escapeHtml(data.ifb_qdisc || 'No IFB qdisc data')}</pre>`)}
    `;
  }
};

window.QosActions = {
  readForm() {
    return {
      wan: document.getElementById('qos-wan').value.trim(),
      download: document.getElementById('qos-download').value.trim(),
      upload: document.getElementById('qos-upload').value.trim(),
      diffserv: document.getElementById('qos-diffserv').value,
      overhead: document.getElementById('qos-overhead').value.trim() || '0',
      mpu: document.getElementById('qos-mpu').value.trim() || '0',
      rtt: document.getElementById('qos-rtt').value.trim(),
      nat: document.getElementById('qos-nat').checked ? 'true' : 'false',
      ack_filter: document.getElementById('qos-ack').checked ? 'true' : 'false',
      wash: document.getElementById('qos-wash').checked ? 'true' : 'false',
      split_gso: document.getElementById('qos-split').checked ? 'true' : 'false'
    };
  },

  async saveApply() {
    await NinjakuAPI.post('/qos', this.readForm());
    const r = await NinjakuAPI.post('/qos/apply');

    if (r.ok) {
      UI.toast('success', 'QoS applied', 'CAKE traffic shaping is now active.');
    } else {
      UI.toast('error', 'QoS failed', r.error || 'Unable to apply QoS.');
    }

    await Ninjaku.navigate('qos');
  },

  async disable() {
    const ok = await UI.confirm({
      title: 'Disable QoS?',
      message: 'Traffic shaping will be removed from WAN and IFB.',
      confirmText: 'Disable',
      danger: true
    });

    if (!ok) return;

    await NinjakuAPI.post('/qos/disable');
    UI.toast('success', 'QoS disabled', 'Traffic shaping was removed.');
    await Ninjaku.navigate('qos');
  }
};
