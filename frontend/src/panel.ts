import { LitElement, PropertyValues, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";
import { customElement } from "./define";
import { Strings, loadCatalogue, translate } from "./localize";
import { DEFAULT_SCHEME, applyScheme, followsHaTheme } from "./palettes";
import { baseStyles, themeStyles } from "./styles";
import type { DeviceInfo, Hass, PanelSettings, ViewName, WriteRequest } from "./types";
import "./views/device";
import "./views/overview";
import "./views/settings";

const DOMAIN = "goalake_poe_switch";
const DEFAULTS: PanelSettings = { scheme: DEFAULT_SCHEME, mode: "auto", language: "auto", device: "" };

@customElement("goalake-poe-switch-panel")
export class GoalakePoeSwitchPanel extends LitElement {
  @property({ attribute: false }) hass!: Hass;
  @property({ type: Boolean }) narrow = false;

  @state() private _devices: DeviceInfo[] = [];
  @state() private _view: ViewName = "overview";
  @state() private _settings: PanelSettings = { ...DEFAULTS };
  @state() private _catalogue: Strings = {};
  @state() private _error = "";
  private _started = false;
  private _unsub?: () => Promise<void>;
  private _saveTimer?: number;
  private _errorTimer?: number;

  static styles = [
    themeStyles,
    baseStyles,
    css`
      :host {
        background: var(--gp-bg);
        min-height: 100vh;
      }
      header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 16px;
        border-bottom: 1px solid var(--gp-line);
        background: var(--gp-surface);
        flex-wrap: wrap;
        position: sticky;
        top: 0;
        z-index: 5;
      }
      .menu {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 22px;
        padding: 0 4px;
      }
      .brand {
        font-weight: 700;
        letter-spacing: 0.04em;
      }
      nav {
        display: flex;
        gap: 6px;
        margin-left: auto;
      }
      nav button {
        background: none;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 6px 12px;
        cursor: pointer;
        color: var(--gp-fg-2);
      }
      nav button.active {
        color: var(--gp-accent);
        border-color: var(--gp-accent);
      }
      main {
        padding: 16px;
        max-width: 1200px;
        margin: 0 auto;
      }
      .error {
        background: var(--gp-magenta-wash);
        border: 1px solid var(--gp-crit);
        color: var(--gp-crit);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 12px;
      }
    `,
  ];

  protected willUpdate(changed: PropertyValues): void {
    if (changed.has("hass") && this.hass && !this._started) {
      this._started = true;
      void this._start();
    }
    if (changed.has("hass") || changed.has("_settings")) void this._loadLanguage();
  }

  protected updated(): void {
    const s = this._settings;
    const light = s.mode === "light" || (s.mode === "auto" && this.hass?.themes?.darkMode === false);
    this.toggleAttribute("light", !followsHaTheme(s.scheme) && light);
    applyScheme(this, s.scheme, light);
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    void this._unsub?.();
    this._unsub = undefined;
    this._started = false;
  }

  private async _start(): Promise<void> {
    try {
      const stored = await this.hass.callWS<Partial<PanelSettings>>({ type: `${DOMAIN}/settings/get` });
      this._settings = { ...DEFAULTS, ...stored };
      this._unsub = await this.hass.connection.subscribeMessage<{ devices: DeviceInfo[] }>(
        (msg) => {
          this._devices = msg.devices;
        },
        { type: `${DOMAIN}/subscribe` },
      );
    } catch (err) {
      this._showError(this._t("error.load", { message: this._message(err) }));
    }
  }

  private async _loadLanguage(): Promise<void> {
    const code = this._settings.language === "auto" ? this.hass?.language ?? "en" : this._settings.language;
    this._catalogue = await loadCatalogue(code);
  }

  private _t = (key: string, values?: Record<string, string | number>): string => translate(this._catalogue, key, values);

  private _message(err: unknown): string {
    if (err && typeof err === "object" && "message" in err) return String((err as { message: unknown }).message);
    return String(err);
  }

  private _showError(text: string): void {
    this._error = text;
    window.clearTimeout(this._errorTimer);
    this._errorTimer = window.setTimeout(() => (this._error = ""), 9000);
  }

  private _change(partial: Partial<PanelSettings>): void {
    this._settings = { ...this._settings, ...partial };
    window.clearTimeout(this._saveTimer);
    this._saveTimer = window.setTimeout(() => {
      void this.hass.callWS({ type: `${DOMAIN}/settings/set`, settings: this._settings }).catch(() => undefined);
    }, 400);
  }

  private async _write(entryId: string, request: WriteRequest): Promise<void> {
    try {
      await this.hass.callWS({ type: `${DOMAIN}/write`, entry_id: entryId, ...request });
    } catch (err) {
      this._showError(this._t("error.write", { message: this._message(err) }));
    }
  }

  private get _selectedId(): string {
    const wanted = this._settings.device;
    return this._devices.some((d) => d.entry_id === wanted) ? wanted : this._devices[0]?.entry_id ?? "";
  }

  render() {
    const admin = Boolean(this.hass?.user?.is_admin);
    const nav: [ViewName, string][] = [
      ["overview", "nav.overview"],
      ["device", "nav.device"],
      ["settings", "nav.settings"],
    ];
    return html`
      <header>
        ${this.narrow
          ? html`<button class="menu" aria-label="menu" @click=${() => this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }))}>☰</button>`
          : nothing}
        <span class="brand">${this._t("app.title")}</span>
        <nav>${nav.map(([view, key]) => html`<button class=${this._view === view ? "active" : ""} @click=${() => (this._view = view)}>${this._t(key)}</button>`)}</nav>
      </header>
      <main
        @write=${(e: CustomEvent<{ entry_id: string; request: WriteRequest }>) => void this._write(e.detail.entry_id, e.detail.request)}
        @open-device=${(e: CustomEvent<string>) => {
          this._change({ device: e.detail });
          this._view = "device";
        }}
        @select-device=${(e: CustomEvent<string>) => this._change({ device: e.detail })}
        @settings-change=${(e: CustomEvent<Partial<PanelSettings>>) => this._change(e.detail)}
      >
        ${this._error ? html`<div class="error" role="alert">${this._error}</div>` : nothing}
        ${this._view === "overview" ? html`<gp-overview .t=${this._t} .devices=${this._devices}></gp-overview>` : nothing}
        ${this._view === "device" ? html`<gp-device .t=${this._t} .admin=${admin} .devices=${this._devices} .selectedId=${this._selectedId}></gp-device>` : nothing}
        ${this._view === "settings" ? html`<gp-settings .t=${this._t} .admin=${admin} .settings=${this._settings} .devices=${this._devices} .selectedId=${this._selectedId}></gp-settings>` : nothing}
      </main>
    `;
  }
}
