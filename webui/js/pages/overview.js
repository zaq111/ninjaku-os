window.Pages = window.Pages || {};

Pages.overview = {
  title: 'Overview',
  subtitle: 'Here is what is happening with your network today.',

  async render() {
    const [router, firewall, dhcp, devices, qos] = await Promise.all([
      NinjakuAPI.get('/router'),
      NinjakuAPI.get('/firewall'),
      NinjakuAPI.get('/dhcp'),
      NinjakuAPI.get('/devices'),
      NinjakuAPI.get('/qos')
    ]);

    const deviceList = devices.devices || [];
    const online = devices.online ?? deviceList.filter(d => d.status === 'online').length;
    const idle = devices.idle ?? deviceList.filter(d => d.status === 'idle').length;
    const away = devices.away ?? deviceList.filter(d => d.status === 'away').length;
    const offline = devices.offline ?? deviceList.filter(d => d.status === 'offline').length;

    const total = devices.count || deviceList.length || 0;
    const healthOk = router.state === 'running' && router.ip_forward === '1' && firewall.nft_ok && dhcp.service === 'active';

    const activeDevices = deviceList
      .filter(d => ['online', 'idle'].includes(d.status))
      .slice(0, 6);

    const activeRows = activeDevices.map(d => `
      <div class="activity-item">
        <div class="activity-dot"></div>
        <div>
          <strong>${escapeHtml(d.alias || d.hostname || d.mac || 'Unknown')}</strong><br>
          <span>${escapeHtml(d.ip || '-')} · ${escapeHtml(d.profile || 'default')} · ${escapeHtml(d.last_seen_age || '-')}</span>
        </div>
        <strong>${escapeHtml(d.status || 'unknown')}</strong>
      </div>
    `).join('');

    const qr = qos.queue_runtime || {};
    const qosRuntime = qos.runtime || {};
    const queueRows = (qr.flows || []).slice(0, 6).map(f => `
      <div class="activity-item">
        <div class="activity-dot"></div>
        <div>
          <strong>${escapeHtml(f.queue || '-')}</strong><br>
          <span>${escapeHtml(f.client_name || f.client_ip || '-')} → ${escapeHtml(f.destination || '-')} · ${escapeHtml(f.proto || '')}/${escapeHtml(f.destination_port || '')}</span>
        </div>
        <strong>${escapeHtml(f.dscp || '-')}</strong>
      </div>
    `).join('');

    return `
      <div class="hero">
        <div>
          <h2>Good day, admin 👋</h2>
          <p>${router.state === 'running' ? 'Everything looks operational.' : 'Ninjaku needs your attention.'}</p>
        </div>
        <div>
          <button class="icon-button" onclick="Ninjaku.refresh()">↻</button>
          <button class="primary-button" onclick="Ninjaku.applyPolicy()">Apply Policy</button>
        </div>
      </div>

      <section class="grid grid-6" style="margin-bottom:18px">
        ${UI.statCard({ icon: healthOk ? '✓' : '!', color: healthOk ? 'green' : 'red', label: 'Health', value: healthOk ? 'Healthy' : 'Needs Check', sub: router.state || 'unknown' })}
        ${UI.statCard({ icon: '🌐', color: statusColor(router.wan_state), label: 'WAN', value: router.wan_state || 'unknown', sub: router.wan || '-' })}
        ${UI.statCard({ icon: '⇆', color: router.ip_forward === '1' ? 'green' : 'red', label: 'Forwarding', value: router.ip_forward === '1' ? 'Enabled' : 'Disabled', sub: 'IPv4 routing' })}
        ${UI.statCard({ icon: '▣', color: online > 0 ? 'purple' : 'gray', label: 'Clients', value: online, sub: `${total} total · ${idle} idle · ${offline + away} away/offline` })}
        ${UI.statCard({ icon: '🛡', color: firewall.nft_ok ? 'green' : 'red', label: 'Firewall', value: firewall.nft_ok ? 'OK' : 'Failed', sub: 'nftables' })}
        ${UI.statCard({ icon: '⇄', color: statusColor(dhcp.service), label: 'DHCP', value: dhcp.service || 'unknown', sub: 'dnsmasq' })}
      </section>

      ${UI.panel('Network Topology', `
        <div class="topology-box">
          <div class="topology-node ${router.wan_state === 'UP' ? 'ok' : 'bad'}">
            <div class="topology-icon">🌐</div>
            <strong>WAN</strong>
            <span>${escapeHtml(router.wan || '-')}</span>
            <small>${escapeHtml(router.wan_state || 'unknown')}</small>
          </div>

          <div class="topology-line"></div>

          <div class="topology-node ${healthOk ? 'ok' : 'warn'}">
            <div class="topology-icon">🥷</div>
            <strong>Ninjaku OS</strong>
            <span>${router.ip_forward === '1' ? 'Forwarding ON' : 'Forwarding OFF'}</span>
            <small>${escapeHtml(router.state || 'unknown')}</small>
          </div>

          <div class="topology-line"></div>

          <div class="topology-node ${online > 0 ? 'ok' : 'warn'}">
            <div class="topology-icon">▣</div>
            <strong>Clients</strong>
            <span>${online} online</span>
            <small>${total} total devices</small>
          </div>
        </div>
      `)}

      ${UI.panel('Active Devices', `
        <div class="activity-list">
          ${activeRows || '<div class="activity-item"><div class="activity-dot"></div><div>No active devices right now</div><span>-</span></div>'}
        </div>
      `)}

      ${UI.panel('QoS Queue Live', `
        <div class="device-detail-grid" style="margin-bottom:12px">
          <div><span>Strategy</span><strong>${escapeHtml(qosRuntime.strategy_effective || '-')}</strong></div>
          <div><span>DiffServ</span><strong>${escapeHtml(qosRuntime.diffserv_active || '-')}</strong></div>
          <div><span>Limiter</span><strong>${qosRuntime.limiter_active ? 'Active' : 'Inactive'}</strong></div>
          <div><span>Queue Monitor</span><strong>${qr.enabled === false ? 'Off' : 'On'}</strong></div>
        </div>
        <div class="activity-list">
          ${queueRows || '<div class="activity-item"><div class="activity-dot"></div><div>No queue samples. Enable Runtime Monitor in QoS to see live flows.</div><span>-</span></div>'}
        </div>
      `)}

      <section class="grid grid-2">
        ${UI.panel('Network Interfaces', `
          <div class="activity-list">
            <div class="activity-item"><div class="activity-dot"></div><div><strong>WAN (${escapeHtml(router.wan)})</strong><br><span>${escapeHtml(router.wan_state)} · upstream interface</span></div><strong>${escapeHtml(router.wan)}</strong></div>
            <div class="activity-item"><div class="activity-dot"></div><div><strong>LAN (${escapeHtml(router.lan)})</strong><br><span>${escapeHtml(router.lan_state)} · DHCP network</span></div><strong>${escapeHtml(router.lan_ip)}</strong></div>
            <div class="activity-item"><div class="activity-dot"></div><div><strong>Firewall</strong><br><span>nftables status</span></div><strong>${firewall.nft_ok ? 'OK' : 'Failed'}</strong></div>
            <div class="activity-item"><div class="activity-dot"></div><div><strong>DHCP</strong><br><span>LAN address assignment</span></div><strong>${escapeHtml(dhcp.service)}</strong></div>
          </div>
        `)}

        ${UI.panel('System Activity', `
          <div class="activity-list">
            <div class="activity-item"><div class="activity-dot"></div><div>Router state is ${escapeHtml(router.state)}</div><span>now</span></div>
            <div class="activity-item"><div class="activity-dot"></div><div>Firewall ruleset checked</div><span>now</span></div>
            <div class="activity-item"><div class="activity-dot"></div><div>${online} device(s) online</div><span>now</span></div>
            <div class="activity-item"><div class="activity-dot"></div><div>DHCP service is ${escapeHtml(dhcp.service)}</div><span>now</span></div>
          </div>
        `)}
      </section>
    `;
  }
};
