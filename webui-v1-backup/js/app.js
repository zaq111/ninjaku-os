window.Ninjaku = {
  currentPage: 'overview',
  menu: [],

  async init() {
    await this.loadMenu();
    const initial = location.hash ? location.hash.substring(1) : 'overview';
    await this.navigate(initial);
    window.addEventListener('hashchange', async () => {
      const page = location.hash ? location.hash.substring(1) : 'overview';
      await this.navigate(page, false);
    });
  },

  async loadMenu() {
    try {
      const data = await NinjakuAPI.get('/modules');
      this.menu = data.modules || [];
    } catch (err) {
      this.menu = [
        { id: 'overview', title: 'Overview', page: 'overview', order: 0 },
        { id: 'router', title: 'Router', page: 'router', order: 10 },
        { id: 'devices', title: 'Devices', page: 'devices', order: 20 },
        { id: 'policy', title: 'Policy', page: 'policy', order: 30 },
        { id: 'profiles', title: 'Profiles', page: 'profiles', order: 40 },
        { id: 'settings', title: 'Settings', page: 'settings', order: 90 }
      ];
    }

    this.renderMenu();
  },

  renderMenu() {
    const nav = document.getElementById('sidebar-menu');
    nav.innerHTML = this.menu.map(item => `
      <a href="#${item.page || item.id}" data-page="${item.page || item.id}">
        ${escapeHtml(item.title || item.id)}
      </a>
    `).join('');
  },

  async navigate(page, updateHash = true) {
    if (!Pages[page]) page = 'overview';
    this.currentPage = page;

    if (updateHash && location.hash !== '#' + page) {
      location.hash = page;
      return;
    }

    document.querySelectorAll('nav a').forEach(a => {
      a.classList.toggle('active', a.dataset.page === page);
    });

    document.getElementById('page-title').textContent = Pages[page].title || page;
    document.getElementById('page-subtitle').textContent = Pages[page].subtitle || '';

    const content = document.getElementById('content');
    content.innerHTML = '<section class="panel"><h3>Loading...</h3></section>';

    try {
      content.innerHTML = await Pages[page].render();
    } catch (err) {
      content.innerHTML = `<section class="panel"><h3 class="fail">Error</h3><p>${escapeHtml(err.message)}</p></section>`;
    }
  },

  async refresh() {
    await this.navigate(this.currentPage, false);
  }
};

window.addEventListener('DOMContentLoaded', () => Ninjaku.init());
setInterval(() => Ninjaku.refresh(), 10000);
