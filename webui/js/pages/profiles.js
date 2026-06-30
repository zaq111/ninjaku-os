window.Pages = window.Pages || {};

Pages.profiles = {
  title: 'Profiles',
  subtitle: 'System and custom device profiles',

  async render() {
    const data = await NinjakuAPI.get('/profiles');
    const cards = (data.profiles || []).map(p => `
      <div class="card">
        <span>${p.is_system ? 'System Profile' : 'Custom Profile'}</span>
        <strong>${escapeHtml(p.name)}</strong>
        <p>${escapeHtml(p.description)}</p>
      </div>
    `).join('');

    return `<section class="grid cards">${cards}</section>`;
  }
};
