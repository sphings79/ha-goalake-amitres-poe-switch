/** Lovelace card: ports, power and (for administrators) PoE switching of one switch. */

import { LitElement, PropertyValues, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";
import "./components/gp-confirm";
import "./components/gp-port-grid";
import { customElement } from "./define";
import { watts } from "./format";
import { Strings, loadCatalogue, translate } from "./localize";
import { SCHEMES, applyScheme, followsHaTheme } from "./palettes";
import { baseStyles, themeStyles } from "./styles";
import type { DeviceInfo, Hass } from "./types";

const DOMAIN = "goalake_poe_switch";
const CARD_TYPE = "goalake-poe-switch-card";

export interface CardConfig {
  type: string;
  entry_id?: string;
  title?: string;
  /** Printed port labels to show; all ports when absent. */
  ports?: string[];
  interactive?: boolean;
  /** Palette id; "ha" (default) follows the Home Assistant theme. */
  scheme?: string;
}

@customElement(CARD_TYPE)
export class GoalakePoeSwitchCard extends LitElement {
  @property({ attribute: false }) hass!: Hass;
  @state() private _config: CardConfig = { type: `custom:${CARD_TYPE}` };
  @state() private _devices: DeviceInfo[] = [];
  @state() private _catalogue: Strings = {};
  @state() private _error = "";
  @state() private _confirm: { index: number; label: string } | null = null;
  private _unsub?: () => Promise<void>;
  private _subscribing = false;

  static styles = [
    themeStyles,
    baseStyles,
    css`
      ha-card {
        padding: 14px 16px;
        background: var(--gp-surface);
        color: var(--gp-fg);
      }
      .head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 8px;
      }
      .title {
        font-weight: 600;
        font-size: 16px;
      }
      .stats {
        display: flex;
        gap: 24px;
        margin-bottom: 12px;
      }
      .error {
        color: var(--gp-crit);
        font-size: 13px;
        margin-top: 8px;
      }
    `,
  ];

  static getConfigElement(): HTMLElement {
    return document.createElement(`${CARD_TYPE}-editor`);
  }

  static getStubConfig(): Partial<CardConfig> {
    return { interactive: false };
  }

  setConfig(config: CardConfig): void {
    this._config = { ...config };
  }

  getCardSize(): number {
    return 3;
  }

  connectedCallback(): void {
    super.connectedCallback();
    if (this.hass) void this._subscribe();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    void this._unsub?.();
    this._unsub = undefined;
  }

  protected willUpdate(changed: PropertyValues): void {
    if (changed.has("hass") && this.hass) {
      void this._subscribe();
      void loadCatalogue(this.hass.language).then((c) => (this._catalogue = c));
    }
  }

  protected updated(): void {
    const scheme = this._config.scheme ?? "ha";
    const light = this.hass?.themes?.darkMode === false;
    this.toggleAttribute("light", !followsHaTheme(scheme) && light);
    applyScheme(this, scheme, light);
  }

  private async _subscribe(): Promise<void> {
    if (this._unsub || this._subscribing || !this.isConnected) return;
    this._subscribing = true;
    try {
      this._unsub = await this.hass.connection.subscribeMessage<{ devices: DeviceInfo[] }>(
        (msg) => (this._devices = msg.devices),
        { type: `${DOMAIN}/subscribe` },
      );
    } catch {
      this._error = "–";
    } finally {
      this._subscribing = false;
    }
  }

  private _t = (key: string, values?: Record<string, string | number>): string => translate(this._catalogue, key, values);

  private get _device(): DeviceInfo | undefined {
    const id = this._config.entry_id;
    return id ? this._devices.find((d) => d.entry_id === id) : this._devices[0];
  }

  private async _setPoe(index: number, on: boolean): Promise<void> {
    const device = this._device;
    if (!device) return;
    try {
      this._error = "";
      await this.hass.callWS({ type: `${DOMAIN}/write`, entry_id: device.entry_id, action: "poe", index, value: on });
    } catch (err) {
      this._error = err && typeof err === "object" && "message" in err ? String((err as { message: unknown }).message) : String(err);
    }
  }

  private _portClicked(index: number, device: DeviceInfo): void {
    const port = device.ports.find((p) => p.index === index);
    if (!port || !port.is_poe || !this._config.interactive || !this.hass.user?.is_admin) return;
    if (port.poe_enabled) this._confirm = { index, label: port.label };
    else void this._setPoe(index, true);
  }

  render() {
    const d = this._device;
    if (!d) {
      return html`<ha-card><span class="note">${this._t(this._devices.length ? "card.pick" : "card.no_device")}</span></ha-card>`;
    }
    const shown = this._config.ports?.length ? d.ports.filter((p) => this._config.ports!.includes(p.label)) : d.ports;
    const canWrite = Boolean(this._config.interactive && this.hass?.user?.is_admin);
    return html`<ha-card>
      <div class="head">
        <span class="title">${this._config.title || d.title}</span>
        <span class="pill ${d.available ? "ok" : "bad"}">${this._t(d.available ? "state.online" : "state.offline")}</span>
      </div>
      <div class="stats">
        <div><div class="label">${this._t("stat.power")}</div><div class="value">${watts(d.total_power_w)}</div></div>
        <div><div class="label">${this._t("stat.temperature")}</div><div class="value">${d.temperature_c === null ? "–" : `${d.temperature_c.toFixed(1)} °C`}</div></div>
      </div>
      <gp-port-grid .ports=${shown} ?readonly=${!canWrite} @port-select=${(e: CustomEvent<number>) => this._portClicked(e.detail, d)}></gp-port-grid>
      ${this._error ? html`<div class="error" role="alert">${this._error}</div>` : nothing}
      <gp-confirm
        ?open=${this._confirm !== null}
        .heading=${this._t("confirm.title")}
        .message=${this._confirm ? this._t("confirm.poe_off", { port: this._confirm.label }) : ""}
        .okLabel=${this._t("confirm.ok")}
        .cancelLabel=${this._t("confirm.cancel")}
        @cancel=${() => (this._confirm = null)}
        @confirm=${() => {
          const c = this._confirm;
          this._confirm = null;
          if (c) void this._setPoe(c.index, false);
        }}
      ></gp-confirm>
    </ha-card>`;
  }
}

/** The editor Home Assistant shows when the card is added or edited in the UI. */
@customElement(`${CARD_TYPE}-editor`)
export class GoalakePoeSwitchCardEditor extends LitElement {
  @property({ attribute: false }) hass!: Hass;
  @state() private _config: CardConfig = { type: `custom:${CARD_TYPE}` };
  @state() private _devices: DeviceInfo[] = [];
  @state() private _catalogue: Strings = {};
  private _loaded = false;

  static styles = [
    baseStyles,
    css`
      :host {
        display: block;
      }
      .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        margin-bottom: 14px;
      }
      .ports {
        display: flex;
        flex-wrap: wrap;
        gap: 6px 14px;
      }
      label.check {
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--primary-text-color);
      }
      select,
      input[type="text"] {
        font: inherit;
        padding: 8px 10px;
        border-radius: 6px;
        border: 1px solid var(--divider-color, #888);
        background: var(--card-background-color, #fff);
        color: var(--primary-text-color);
      }
      .label {
        color: var(--secondary-text-color);
      }
    `,
  ];

  setConfig(config: CardConfig): void {
    this._config = { ...config };
  }

  protected willUpdate(changed: PropertyValues): void {
    if (changed.has("hass") && this.hass && !this._loaded) {
      this._loaded = true;
      void this.hass
        .callWS<DeviceInfo[]>({ type: `${DOMAIN}/devices` })
        .then((d) => (this._devices = d))
        .catch(() => undefined);
      void loadCatalogue(this.hass.language).then((c) => (this._catalogue = c));
    }
  }

  private _t = (key: string): string => translate(this._catalogue, key);

  private _change(partial: Partial<CardConfig>): void {
    const config = { ...this._config, ...partial };
    for (const key of Object.keys(config) as (keyof CardConfig)[]) {
      const v = config[key];
      if (v === undefined || v === "" || (Array.isArray(v) && v.length === 0)) delete config[key];
    }
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }

  private get _device(): DeviceInfo | undefined {
    const id = this._config.entry_id;
    return id ? this._devices.find((d) => d.entry_id === id) : this._devices[0];
  }

  render() {
    const device = this._device;
    // printed order: PoE ports 1..n, then LAN1, LAN2
    const labels = device
      ? [...device.ports].sort((a, b) => Number(b.is_poe) - Number(a.is_poe) || (a.is_poe ? Number(a.label) - Number(b.label) : a.label.localeCompare(b.label))).map((p) => p.label)
      : [];
    const selected = this._config.ports?.length ? this._config.ports : labels;
    return html`
      <div class="field">
        <span class="label">${this._t("card.device")}</span>
        <select @change=${(e: Event) => this._change({ entry_id: (e.target as HTMLSelectElement).value, ports: undefined })}>
          ${this._devices.map((d) => html`<option value=${d.entry_id} ?selected=${d.entry_id === device?.entry_id}>${d.title}</option>`)}
        </select>
      </div>
      <div class="field">
        <span class="label">${this._t("card.title")}</span>
        <input type="text" .value=${this._config.title ?? ""} @input=${(e: Event) => this._change({ title: (e.target as HTMLInputElement).value })} />
      </div>
      <div class="field">
        <span class="label">${this._t("card.ports")}</span>
        <div class="ports">
          ${labels.map(
            (l) => html`<label class="check"><input type="checkbox" .checked=${selected.includes(l)} @change=${(e: Event) => this._togglePort(l, (e.target as HTMLInputElement).checked, labels, selected)} />${l}</label>`,
          )}
        </div>
      </div>
      <div class="field">
        <label class="check"><input type="checkbox" .checked=${Boolean(this._config.interactive)} @change=${(e: Event) => this._change({ interactive: (e.target as HTMLInputElement).checked || undefined })} />${this._t("card.interactive")}</label>
      </div>
      <div class="field">
        <span class="label">${this._t("card.scheme")}</span>
        <select @change=${(e: Event) => this._change({ scheme: (e.target as HTMLSelectElement).value === "ha" ? undefined : (e.target as HTMLSelectElement).value })}>
          ${[...SCHEMES].sort((a, b) => (a.id === "ha" ? -1 : b.id === "ha" ? 1 : 0)).map((s) => html`<option value=${s.id} ?selected=${(this._config.scheme ?? "ha") === s.id}>${s.name}</option>`)}
        </select>
      </div>
    `;
  }

  private _togglePort(label: string, on: boolean, all: string[], current: string[]): void {
    const next = on ? [...new Set([...current, label])] : current.filter((l) => l !== label);
    // every port selected means "no filter"
    this._change({ ports: next.length === all.length ? undefined : next });
  }
}

declare global {
  interface Window {
    customCards?: { type: string; name: string; description: string; preview?: boolean }[];
  }
}
window.customCards = window.customCards ?? [];
if (!window.customCards.some((c) => c.type === CARD_TYPE)) {
  window.customCards.push({
    type: CARD_TYPE,
    name: "PoE Switch",
    description: "Ports, power and PoE control of a Goalake / Amitres PoE switch",
    preview: false,
  });
}
