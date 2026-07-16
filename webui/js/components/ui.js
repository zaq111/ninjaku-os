window.UI = {
  icon(name) {
    const icons = {
      overview: "⌂",
      router: "⛓",
      devices: "▣",
      policy: "♢",
      profiles: "♧",
      settings: "⚙",
      firewall: "🛡",
      dns_filter: "🛡",
      dhcp: "⇄",
      leases: "⇄",
      wifi: "📶",
      network: "☍",
      qos: "⚡",
      vpn: "◇",
      wireguard: "◇",
      tailscale: "◉",
      adguard: "🛡",
      healthy: "✓",
      uptime: "◷",
      cpu: "◉",
      memory: "▣",
      wan: "🌐",
      lan: "⛓"
    };
    return icons[name] || "•";
  },

  badge(text, color = "") {
    return `<span class="badge ${color}">${escapeHtml(text)}</span>`;
  },

  statCard({ icon = "•", color = "blue", label = "", value = "", sub = "" }) {
    return `
      <div class="card">
        <div class="card-icon icon-${color}">${icon}</div>
        <div>
          <small>${escapeHtml(label)}</small>
          <strong>${escapeHtml(value)}</strong>
          <span>${escapeHtml(sub)}</span>
        </div>
      </div>
    `;
  },

  kv(label, value) {
    return `<div class="kv-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
  },

  panel(title, body, action = "") {
    return `
      <section class="panel">
        <div class="panel-head">
          <h3>${escapeHtml(title)}</h3>
          ${action}
        </div>
        ${body}
      </section>
    `;
  }
};

UI.empty = function(title = "No data", message = "There is nothing to show yet.") {
  return `<div class="empty-state"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span></div>`;
};

UI.loading = function(message = "Loading...") {
  return `<section class="loading-state">${escapeHtml(message)}</section>`;
};

UI.toast = function(type = "info", title = "", message = "") {
  let root = document.getElementById("toast-root");

  if (!root) {
    root = document.createElement("div");
    root.id = "toast-root";
    root.className = "toast-root";
    document.body.appendChild(root);
  }

  const icon = type === "success" ? "✓" : (type === "error" ? "!" : "i");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div>
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(message)}</span>
    </div>
  `;

  root.appendChild(el);
  setTimeout(() => el.remove(), 5000);
};

UI.confirm = function({ title = "Confirm action", message = "", confirmText = "Confirm", danger = false } = {}) {
  return new Promise(resolve => {
    const root = document.getElementById("modal-root");
    if (!root) return resolve(false);

    root.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal">
          <div class="modal-head"><h3>${escapeHtml(title)}</h3></div>
          <div class="modal-body">${escapeHtml(message)}</div>
          <div class="modal-actions">
            <button class="soft-button" id="modal-cancel">Cancel</button>
            <button class="${danger ? "danger-button" : "primary-button"}" id="modal-confirm">${escapeHtml(confirmText)}</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById("modal-cancel").onclick = () => {
      root.innerHTML = "";
      resolve(false);
    };

    document.getElementById("modal-confirm").onclick = () => {
      root.innerHTML = "";
      resolve(true);
    };
  });
};

UI.busy = {
  show(title = "Processing...", message = "Please wait.") {
    let root = document.getElementById("busy-root");

    if (!root) {
      root = document.createElement("div");
      root.id = "busy-root";
      document.body.appendChild(root);
    }

    root.innerHTML = `
      <div class="busy-backdrop">
        <div class="busy-box">
          <div class="busy-spinner"></div>
          <h3>${escapeHtml(title)}</h3>
          <p>${escapeHtml(message)}</p>
        </div>
      </div>
    `;
  },

  hide() {
    const root = document.getElementById("busy-root");
    if (root) root.innerHTML = "";
  }
};

