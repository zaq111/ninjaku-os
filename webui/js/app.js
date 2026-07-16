window.Ninjaku = {
  currentPage: "overview",
  menu: [],

  async init() {
    if (localStorage.getItem("ninjaku.sidebarCollapsed") === "1") {
      document.body.classList.add("sidebar-collapsed");
    }

    await this.loadMenu();

    const initial = location.hash ? location.hash.substring(1) : "overview";
    await this.navigate(initial);

    window.addEventListener("hashchange", async () => {
      const page = location.hash ? location.hash.substring(1) : "overview";
      await this.navigate(page, false);
    });
  },

  async loadMenu() {
    try {
      const data = await NinjakuAPI.get("/modules");
      this.menu = data.modules || [];
    } catch {
      this.menu = [
        { id: "overview", title: "Overview", page: "overview", icon: "⌂" },
        { id: "router", title: "Router", page: "router", icon: "⛓" },
        { id: "devices", title: "Devices", page: "devices", icon: "▣" },
        { id: "policy", title: "Policy", page: "policy", icon: "♢" },
        { id: "profiles", title: "Profiles", page: "profiles", icon: "♧" },
        { id: "settings", title: "Settings", page: "settings", icon: "⚙" },
        { id: "adguard", title: "AdGuard", page: "adguard", icon: "🛡" },
        { id: "tailscale", title: "Tailscale", page: "tailscale", icon: "◉" },
        { id: "wireguard", title: "WireGuard", page: "wireguard", icon: "◇" },
        { id: "qos", title: "QoS", page: "qos", icon: "⚡" }
      ];
    }

    this.renderMenu();
  },

  renderMenu() {
    const nav = document.getElementById("sidebar-menu");
    nav.innerHTML = this.menu.map(item => {
      const page = item.page || item.id;
      const label = item.title || item.id;
      const icon = item.icon || UI.icon(item.id);

      return `
        <a href="#${page}" data-page="${page}" title="${escapeHtml(label)}" aria-label="${escapeHtml(label)}">
          <span>${icon}</span>
          <span>${escapeHtml(label)}</span>
        </a>
      `;
    }).join("");
  },

  async navigate(page, updateHash = true) {
    if (!Pages[page]) page = "overview";
    this.currentPage = page;

    if (updateHash && location.hash !== "#" + page) {
      location.hash = page;
      return;
    }

    document.querySelectorAll(".sidebar-menu a").forEach(a => {
      a.classList.toggle("active", a.dataset.page === page);
    });

    document.getElementById("page-title").textContent = Pages[page].title || page;
    document.getElementById("page-subtitle").textContent = Pages[page].subtitle || "";

    const content = document.getElementById("content");
    content.innerHTML = UI.loading("Loading page...");

    try {
      content.innerHTML = await Pages[page].render();
      await this.updateSidebarState();
    } catch (err) {
      content.innerHTML = UI.panel("Error", `<p class="fail">${escapeHtml(err.message)}</p>`);
      UI.toast("error", "Page error", err.message);
    }
  },

  async updateSidebarState() {
    try {
      const r = await NinjakuAPI.get("/router");
      document.getElementById("sidebar-router-state").textContent = r.state || "unknown";
    } catch {}
  },

  async refresh() {
    await this.navigate(this.currentPage, false);
  },

  async applyPolicy() {
    await NinjakuAPI.post("/policy/apply");
    UI.toast("success", "Policy applied", "Firewall and policy rules were refreshed.");
    await this.refresh();
  },

  toggleSidebar() {
    const shell = document.querySelector(".app-shell");
    if (shell) {
      shell.classList.toggle("sidebar-open");
    }

    document.body.classList.toggle("sidebar-collapsed");
    localStorage.setItem(
      "ninjaku.sidebarCollapsed",
      document.body.classList.contains("sidebar-collapsed") ? "1" : "0"
    );
  }
};

window.NinjakuToggleSidebar = function () {
  window.Ninjaku.toggleSidebar();
};

document.addEventListener("DOMContentLoaded", () => Ninjaku.init());
// Full page auto-refresh disabled: it interrupts forms and causes page blinking.
// Pages that need live data should implement their own lightweight polling.
