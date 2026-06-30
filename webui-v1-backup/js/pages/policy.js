window.Pages = window.Pages || {};

Pages.policy = {
  title: 'Policy',
  subtitle: 'Profile-based policy engine',

  async render() {
    const data = await NinjakuAPI.get('/policy');
    const rows = (data.policies || []).map(p => `
      <tr>
        <td>${escapeHtml(p.profile)}</td>
        <td>${escapeHtml(p.internet)}</td>
        <td>${escapeHtml(p.bandwidth)}</td>
        <td>${escapeHtml(p.dns_filter)}</td>
        <td>${escapeHtml(p.schedule)}</td>
        <td>${escapeHtml(p.priority)}</td>
      </tr>
    `).join('');

    return `
      <section class="panel">
        <h3>Policies</h3>
        <table>
          <thead><tr><th>Profile</th><th>Internet</th><th>Bandwidth</th><th>DNS</th><th>Schedule</th><th>Priority</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </section>
    `;
  }
};
