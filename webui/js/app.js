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
    } catch {
      this.menu = [
        { id: 'overview', title: 'Overview', page: 'overview' },
        { id: 'router', title: 'Router', page: 'router' },
        { id: 'devices', title: 'Devices', page: 'devices' },
        { id: 'policy', title: 'Policy', page: 'policy' },
        { id: 'profiles', title: 'Profiles', page: 'profiles' },
        { id: 'settings', title: 'Settings', page: 'settings' }
      ];
    }

    this.renderMenu();
  },

  renderMenu() {
    const nav = document.getElementById('sidebar-menu');
    nav.innerHTML = this.menu.map(item => {
      const page = item.page || item.id;
      return `
        <a href="#${page}" data-page="${page}">
          <span>${UI.icon(item.icon || item.id)}</span>
          <span>${escapeHtml(item.title || item.id)}</span>
        </a>
      `;
    }).join('');
  },

  async navigate(page, updateHash = true) {
    if (!Pages[page]) page = 'overview';
    this.currentPage = page;

    if (updateHash && location.hash !== '#' + page) {
      location.hash = page;
      return;
    }

    document.querySelectorAll('.sidebar-menu a').forEach(a => {
      a.classList.toggle('active', a.dataset.page === page);
    });

    document.getElementById('page-title').textContent = Pages[page].title || page;
    document.getElementById('page-subtitle').textContent = Pages[page].subtitle || '';

    const content = document.getElementById('content');
    content.innerHTML = UI.loading('Loading page...');

    try {
      content.innerHTML = await Pages[page].render();
      await this.updateSidebarState();
    } catch (err) {
      content.innerHTML = UI.panel('Error', `<p class="fail">${escapeHtml(err.message)}</p>`); UI.toast('error', 'Page error', err.message);
    }
  },

  async updateSidebarState() {
    try {
      const r = await NinjakuAPI.get('/router');
      document.getElementById('sidebar-router-state').textContent = r.state || 'unknown';
    } catch {}
  },

  async refresh() {
    await this.navigate(this.currentPage, false);
  },

  async applyPolicy() {
    await NinjakuAPI.post('/policy/apply');
    UI.toast('success', 'Policy applied', 'Firewall and policy rules were refreshed.');
    await this.refresh();
  },

  toggleSidebar() {
    document.querySelector('.app-shell').classList.toggle('sidebar-open');
  }
};

window.addEventListener('DOMContentLoaded', () => Ninjaku.init());
// Full page auto-refresh disabled: it interrupts forms and causes page blinking.
// Pages that need live data should implement their own lightweight polling.
