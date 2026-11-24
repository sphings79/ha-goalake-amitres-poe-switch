import "/custom_components/goalake_poe_switch/frontend/goalake-poe-switch-panel.js";
import "/custom_components/goalake_poe_switch/frontend/goalake-poe-switch-card.js";

const q = new URLSearchParams(location.search);
const ha = q.get("ha") ?? "dark"; // the Home Assistant theme: dark | light
document.body.className = ha;

// A minimal ha-card, which exists only inside Home Assistant.
customElements.define("ha-card", class extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" }).innerHTML =
      "<style>:host{display:block;border-radius:12px;border:1px solid var(--divider-color,#444);overflow:hidden}</style><slot></slot>";
  }
});

const port = (index, label, o = {}) => ({
  index, label, is_poe: index < 8 && label.length === 1, connected: false, speed_mbps: 0, admin_enabled: true,
  poe_enabled: index < 8 ? true : null, power_w: index < 8 ? 0 : null, tx_kbps: 0, rx_kbps: 0, phy_mode: "1000m_full",
  flow_control: true, priority: 0, limit_up_mbps: 0, limit_down_mbps: 0, ...o,
});
const gps208 = {
  entry_id: "a", title: "GPS208 (4F2A)", available: true, model: "GPS208", firmware: "6.1.260430", voltage_v: 52.3,
  total_power_w: 22.3, temperature_c: 41.2, cloud_status: 0,
  settings: { lldp: 1, storm: 0, watchdog: 1, ai_auto_extend: 0, power_warn: 90 },
  host: "192.168.1.20",
  ports: [
    port(0, "8", { connected: true, speed_mbps: 100, power_w: 0 }),
    port(1, "7", { poe_enabled: true }),
    port(2, "6", { poe_enabled: false }),
    port(3, "5", { connected: true, speed_mbps: 100, power_w: 4.1, tx_kbps: 912, rx_kbps: 88 }),
    port(4, "4", {}),
    port(5, "3", { connected: true, speed_mbps: 100, power_w: 2.1, tx_kbps: 40, rx_kbps: 12 }),
    port(6, "2", { connected: true, speed_mbps: 100, power_w: 11.3, tx_kbps: 2310, rx_kbps: 460 }),
    port(7, "1", { connected: true, speed_mbps: 100, power_w: 4.8, tx_kbps: 3120, rx_kbps: 210 }),
    port(8, "LAN2", { is_poe: false }),
    port(9, "LAN1", { is_poe: false, connected: true, speed_mbps: 1000, tx_kbps: 210, rx_kbps: 6400 }),
  ],
};
const gps204 = {
  ...gps208, entry_id: "b", title: "GPS204 (91C7)", model: "GPS204", total_power_w: 6.4, temperature_c: 37.8, host: "192.168.1.21",
  ports: [
    port(0, "4", { connected: true, speed_mbps: 100, power_w: 6.4, tx_kbps: 1500, rx_kbps: 90 }),
    port(1, "3", {}), port(2, "2", {}), port(3, "1", {}),
    port(4, "LAN2", { is_poe: false }), port(5, "LAN1", { is_poe: false, connected: true, speed_mbps: 1000, tx_kbps: 90, rx_kbps: 1500 }),
  ].map((p, i) => ({ ...p, is_poe: i < 4 })),
};
const devices = q.get("devices") === "1" ? [gps208] : [gps208, gps204];

const hass = {
  language: q.get("lang") ?? "en",
  user: { is_admin: true, name: "Demo" },
  themes: { darkMode: ha === "dark" },
  connection: { subscribeMessage: async (cb) => { cb({ devices }); return async () => {}; } },
  callWS: async (m) => {
    if (m.type.endsWith("/settings/get")) return { scheme: q.get("scheme") ?? "reactor", mode: q.get("mode") ?? "auto", language: "auto", device: "a" };
    if (m.type.endsWith("/devices")) return devices;
    return null;
  },
};

const deep = (root, sel) => {
  const hit = root.querySelector(sel);
  if (hit) return hit;
  for (const el of root.querySelectorAll("*")) if (el.shadowRoot) { const f = deep(el.shadowRoot, sel); if (f) return f; }
  return null;
};
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const stage = document.getElementById("stage");

if ((q.get("kind") ?? "panel") === "card") {
  stage.className = "cards";
  const make = (config) => {
    const card = document.createElement("goalake-poe-switch-card");
    card.setConfig({ type: "custom:goalake-poe-switch-card", ...config });
    card.hass = hass;
    stage.appendChild(card);
  };
  make({ entry_id: "a", interactive: true });
  make({ entry_id: "a", title: "Cameras", ports: ["1", "2", "3", "4"], scheme: "cockpit" });
  make({ entry_id: "b", scheme: "verdant" });
} else {
  const panel = document.createElement("goalake-poe-switch-panel");
  panel.hass = hass;
  stage.appendChild(panel);
  await wait(900);
  const view = q.get("view") ?? "overview";
  const tabs = panel.shadowRoot.querySelectorAll("nav button");
  if (view === "device") tabs[1].click();
  if (view === "settings") tabs[2].click();
  await wait(400);
  if (view === "device") {
    const p = q.get("port");
    if (p) [...deep(panel.shadowRoot, "gp-port-grid").shadowRoot.querySelectorAll("button.port")].find((b) => b.title === p)?.click();
  }
}
