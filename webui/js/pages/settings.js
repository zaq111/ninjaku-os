window.Pages = window.Pages || {};

Pages.settings = {
  title: 'Settings',
  subtitle: 'Ninjaku configuration registry.',

  async render() {
    const data = await NinjakuAPI.get('/settings');
    const rows = (data.settings || []).map(s => `
      <tr><td><strong>${escapeHtml(s.key)}</strong></td><td>${escapeHtml(s.value)}</td></tr>
    `).join('');

    return UI.panel('Settings', `
      <table class="table">
        <thead><tr><th>Key</th><th>Value</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    `);
  }
};
