window.Pages = window.Pages || {};

Pages.settings = {
  title: 'Settings',
  subtitle: 'Ninjaku configuration registry',

  async render() {
    const data = await NinjakuAPI.get('/settings');
    const rows = (data.settings || []).map(s => `
      <tr><td>${escapeHtml(s.key)}</td><td>${escapeHtml(s.value)}</td></tr>
    `).join('');

    return `
      <section class="panel">
        <h3>Settings</h3>
        <table>
          <thead><tr><th>Key</th><th>Value</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </section>
    `;
  }
};
