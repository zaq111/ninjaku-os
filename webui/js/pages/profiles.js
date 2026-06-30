window.Pages = window.Pages || {};

Pages.profiles = {
  title: 'Profiles',
  subtitle: 'System and custom device profiles.',

  async render() {
    const data = await NinjakuAPI.get('/profiles');
    const cards = (data.profiles || []).map(p => `
      <div class="card">
        <div class="card-icon icon-${p.is_system ? 'blue' : 'purple'}">${p.is_system ? '★' : '♢'}</div>
        <div>
          <small>${p.is_system ? 'System Profile' : 'Custom Profile'}</small>
          <strong>${escapeHtml(p.name)}</strong>
          <span>${escapeHtml(p.description)}</span>
        </div>
      </div>
    `).join('');

    return `<section class="grid grid-3">${cards}</section>`;
  }
};
