window.Pages = window.Pages || {};

Pages.policy = {
  title: 'Policy',
  subtitle: 'Profile-based access and bandwidth policy.',

  async render() {
    const data = await NinjakuAPI.get('/policy');
    const rows = (data.policies || []).map(p => `
      <tr>
        <td><strong>${escapeHtml(p.profile)}</strong></td>
        <td>${UI.badge(p.internet, statusColor(p.internet === 'allow' ? 'ok' : 'error'))}</td>
        <td>${escapeHtml(p.bandwidth)}</td>
        <td>${escapeHtml(p.dns_filter)}</td>
        <td>${escapeHtml(p.schedule)}</td>
        <td>${escapeHtml(p.priority)}</td>
      </tr>
    `).join('');

    return UI.panel('Policies', `
      <table class="table">
        <thead><tr><th>Profile</th><th>Internet</th><th>Bandwidth</th><th>DNS</th><th>Schedule</th><th>Priority</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    `);
  }
};
