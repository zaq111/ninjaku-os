async function api(path, options = {}) {
  const res = await fetch('/api/v1' + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  const json = await res.json();
  if (!json.success) throw new Error(json.error?.message || 'API error');
  return json.data;
}

function pretty(obj) {
  return JSON.stringify(obj, null, 2);
}

async function loadRouter() {
  const data = await api('/router');
  document.getElementById('router-state').textContent = data.state || 'unknown';
  document.getElementById('router-state').className =
    data.state === 'running' ? 'ok' : (data.state === 'waiting_for_lan' ? 'warn' : 'fail');
  document.getElementById('router-detail').textContent =
    `${data.wan || '-'} → ${data.lan || '-'} (${data.lan_ip || '-'})`;
  document.getElementById('router-json').textContent = pretty(data);
}

async function loadFirewall() {
  const data = await api('/firewall');
  document.getElementById('firewall-state').textContent = data.nft_ok ? 'OK' : 'FAILED';
  document.getElementById('firewall-state').className = data.nft_ok ? 'ok' : 'fail';
  document.getElementById('firewall-detail').textContent = `IPv4 forward: ${data.ip_forward}`;
}

async function loadDhcp() {
  const data = await api('/dhcp');
  document.getElementById('dhcp-state').textContent = data.service || 'unknown';
  document.getElementById('dhcp-state').className = data.service === 'active' ? 'ok' : 'warn';
  document.getElementById('dhcp-detail').textContent = `enabled: ${data.enabled}`;
}

async function loadDevices() {
  const data = await api('/devices');
  const devices = data.devices || [];
  document.getElementById('device-count').textContent = data.count || 0;

  const tbody = document.getElementById('devices-table');
  tbody.innerHTML = '';

  if (!devices.length) {
    tbody.innerHTML = '<tr><td colspan="6">No devices found.</td></tr>';
    return;
  }

  for (const d of devices) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${d.ip || ''}</td>
      <td>${d.mac || ''}</td>
      <td>${d.status || ''}</td>
      <td>${d.profile || ''}</td>
      <td>${d.policy_internet || ''}</td>
      <td>${d.policy_bandwidth || ''}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadProfiles() {
  const data = await api('/profiles');
  const box = document.getElementById('profiles-list');
  box.innerHTML = '';
  for (const p of data.profiles || []) {
    const s = document.createElement('span');
    s.className = 'badge';
    s.textContent = `${p.name} (${p.is_system ? 'system' : 'custom'})`;
    box.appendChild(s);
  }
}

async function loadPolicy() {
  const data = await api('/policy');
  const box = document.getElementById('policy-list');
  box.innerHTML = '';
  for (const p of data.policies || []) {
    const div = document.createElement('div');
    div.className = 'badge';
    div.textContent = `${p.profile}: ${p.internet}, ${p.bandwidth}, ${p.dns_filter}`;
    box.appendChild(div);
  }
}

async function loadSettings() {
  const data = await api('/settings');
  document.getElementById('settings-json').textContent = pretty(data.settings || []);
}

async function refreshAll() {
  try {
    await Promise.all([
      loadRouter(),
      loadFirewall(),
      loadDhcp(),
      loadDevices(),
      loadProfiles(),
      loadPolicy(),
      loadSettings()
    ]);
  } catch (err) {
    alert(err.message);
  }
}

async function routerEnable() {
  await api('/router/enable', { method: 'POST' });
  await refreshAll();
}

async function routerDisable() {
  if (!confirm('Disable router services? SSH on WAN should remain active.')) return;
  await api('/router/disable', { method: 'POST' });
  await refreshAll();
}

async function devicesSync() {
  await api('/devices/sync', { method: 'POST' });
  await refreshAll();
}

refreshAll();
setInterval(refreshAll, 10000);
