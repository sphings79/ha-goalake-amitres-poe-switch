import { css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";
import { customElement } from "../define";
import { AVAILABLE_LANGUAGES } from "../localize";
import { SCHEMES, schemeById } from "../palettes";
import type { DeviceInfo, ModeSetting, PanelSettings } from "../types";
import { baseStyles } from "../styles";
import "../components/gp-confirm";
import "../components/gp-toggle";
import { ViewBase } from "./view-base";

const FEATURES: [string, string, string][] = [
  ["lldp", "feature.lldp", "lldp"],
  ["storm", "feature.storm", "storm"],
  ["watchdog", "feature.watchdog", "watchdog"],
  ["ai_auto_extend", "feature.ai_auto_extend", "ai_auto_extend"],
];

@customElement("gp-settings")
export class GpSettings extends ViewBase {
  @property({ attribute: false }) settings!: PanelSettings;
  @property({ attribute: false }) devices: DeviceInfo[] = [];
  @property() selectedId = "";
  @state() private _confirmReboot = false;
  @state() private _warn = "";
  private _warnFor = "";

  static styles = [
    baseStyles,
    css`
      .sections {
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        align-items: start;
      }
      .schemes {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 8px;
        margin-bottom: 12px;
      }
      .scheme {
        border: 1px solid var(--gp-line);
        background: var(--gp-surface-2);
        border-radius: 8px;
        padding: 8px;
        cursor: pointer;
        text-align: left;
      }
      .scheme.active {
        border-color: var(--gp-accent);
        box-shadow: 0 0 0 1px var(--gp-accent);
      }
      .swatch {
        display: flex;
        height: 14px;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 6px;
      }
      .swatch span {
        flex: 1;
      }
      .segment {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }
      .warn {
        border-color: var(--gp-warn);
      }
      input[type="number"] {
        width: 90px;
      }
    `,
  ];

  private get _device(): DeviceInfo | undefined {
    return this.devices.find((d) => d.entry_id === this.selectedId) ?? this.devices[0];
  }

  render() {
    const d = this._device;
    return html`<div class="grid sections">
      <div class="card">
        <h2>${this.t("settings.appearance")}</h2>
        <div class="label" style="margin-bottom:6px">${this.t("settings.palette")}</div>
        <div class="schemes">${SCHEMES.map((s) => this._scheme(s.id, s.name))}</div>
        <div class="row">
          <span>${this.t("settings.mode")}</span>
          <span class="segment">
            ${(["auto", "dark", "light"] as ModeSetting[]).map(
              (m) => html`<button class="btn ${this.settings.mode === m ? "primary" : ""}" @click=${() => this.fire("settings-change", { mode: m })}>${this.t(`settings.mode.${m}`)}</button>`,
            )}
          </span>
        </div>
        <div class="row">
          <span>${this.t("settings.language")}</span>
          <select @change=${(e: Event) => this.fire("settings-change", { language: (e.target as HTMLSelectElement).value })}>
            <option value="auto" ?selected=${this.settings.language === "auto"}>${this.t("settings.language.auto")}</option>
            ${AVAILABLE_LANGUAGES.map((l) => html`<option value=${l} ?selected=${this.settings.language === l}>${l.toUpperCase()}</option>`)}
          </select>
        </div>
      </div>
      ${d ? this._features(d) : nothing}
    </div>`;
  }

  private _scheme(id: string, name: string) {
    const s = schemeById(id);
    const colours = id === "ha" ? ["#3b82f6", "#ffffff", "#9ca3af"] : [s.dark.bg, s.dark.accent, s.dark.magenta, s.dark.ok];
    return html`<button class="scheme ${this.settings.scheme === id ? "active" : ""}" @click=${() => this.fire("settings-change", { scheme: id })}>
      <div class="swatch">${colours.map((c) => html`<span style="background:${c}"></span>`)}</div>
      <span>${name}</span>
    </button>`;
  }

  private _features(d: DeviceInfo) {
    const w = (action: string, value: boolean | number) => this.write(d.entry_id, { action, value });
    if (this._warnFor !== d.entry_id) {
      this._warnFor = d.entry_id;
      this._warn = String(d.settings.power_warn ?? 0);
    }
    return html`<div class="card">
        <h2>${this.t("settings.features")} · ${d.title}</h2>
        ${!this.admin ? html`<p class="note">${this.t("admin.required")}</p>` : nothing}
        ${FEATURES.map(
          ([key, label, action]) => html`<div class="row">
            <span>${this.t(label)}</span>
            <gp-toggle .checked=${Boolean(d.settings[key])} ?disabled=${!this.admin} @toggle=${(e: CustomEvent<boolean>) => w(action, e.detail)}></gp-toggle>
          </div>`,
        )}
        <div class="row">
          <span>${this.t("feature.power_warn")}</span>
          <span style="display:flex;gap:8px">
            <input type="number" min="0" max="1000" .value=${this._warn} ?disabled=${!this.admin} @input=${(e: Event) => (this._warn = (e.target as HTMLInputElement).value)} />
            <button class="btn" ?disabled=${!this.admin} @click=${() => w("power_warn", Number(this._warn))}>${this.t("port.apply")}</button>
          </span>
        </div>
      </div>
      <div class="card warn">
        <h2>${this.t("settings.maintenance")}</h2>
        <div class="row">
          <span></span>
          <button class="btn danger" ?disabled=${!this.admin} @click=${() => (this._confirmReboot = true)}>${this.t("settings.reboot")}</button>
        </div>
      </div>
      <gp-confirm
        ?open=${this._confirmReboot}
        .heading=${this.t("confirm.title")}
        .message=${this.t("confirm.reboot")}
        .okLabel=${this.t("confirm.ok")}
        .cancelLabel=${this.t("confirm.cancel")}
        @cancel=${() => (this._confirmReboot = false)}
        @confirm=${() => {
          this._confirmReboot = false;
          this.write(d.entry_id, { action: "reboot", confirm: true });
        }}
      ></gp-confirm>`;
  }
}
