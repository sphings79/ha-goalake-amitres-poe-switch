import { css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";
import { customElement } from "../define";
import { rate, speed, watts } from "../format";
import type { DeviceInfo, PortInfo } from "../types";
import { baseStyles } from "../styles";
import "../components/gp-confirm";
import "../components/gp-port-grid";
import "../components/gp-toggle";
import { ViewBase } from "./view-base";

const MODES = ["down", "10m_half", "10m_full", "100m_half", "100m_full", "1000m_full"];

interface Pending {
  message: string;
  run: () => void;
}

@customElement("gp-device")
export class GpDevice extends ViewBase {
  @property({ attribute: false }) devices: DeviceInfo[] = [];
  @property() selectedId = "";
  @state() private _port: number | null = null;
  @state() private _pending: Pending | null = null;
  @state() private _limitUp = "";
  @state() private _limitDown = "";
  private _limitPort: number | null = null;

  static styles = [
    baseStyles,
    css`
      .tabs {
        display: flex;
        gap: 8px;
        margin-bottom: 12px;
        flex-wrap: wrap;
      }
      .tab {
        padding: 5px 12px;
        border-radius: 999px;
        border: 1px solid var(--gp-line);
        background: var(--gp-surface);
        cursor: pointer;
      }
      .tab.active {
        border-color: var(--gp-accent);
        color: var(--gp-accent);
      }
      .stats {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        margin-bottom: 12px;
      }
      .stat .value {
        font-size: 20px;
      }
      .detail {
        margin-top: 12px;
      }
      .metrics {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
        gap: 10px;
        margin-bottom: 8px;
      }
      .limit {
        display: flex;
        gap: 8px;
        align-items: center;
      }
      .limit input {
        width: 90px;
      }
    `,
  ];

  private get _device(): DeviceInfo | undefined {
    return this.devices.find((d) => d.entry_id === this.selectedId) ?? this.devices[0];
  }

  render() {
    const d = this._device;
    if (!d) return html`<div class="card note">${this.t("overview.empty")}</div>`;
    const port = this._port === null ? undefined : d.ports.find((p) => p.index === this._port);
    return html`
      ${this.devices.length > 1
        ? html`<div class="tabs">
            ${this.devices.map(
              (x) => html`<button class="tab ${x.entry_id === d.entry_id ? "active" : ""}" @click=${() => this._choose(x.entry_id)}>${x.title}</button>`,
            )}
          </div>`
        : nothing}
      <div class="grid stats">
        ${this._stat("stat.power", watts(d.total_power_w))}
        ${this._stat("stat.voltage", d.voltage_v === null ? "–" : `${d.voltage_v} V`)}
        ${this._stat("stat.temperature", d.temperature_c === null ? "–" : `${d.temperature_c.toFixed(1)} °C`)}
        ${this._stat("stat.firmware", d.firmware)}
        ${this._stat("stat.cloud", d.cloud_status === null ? "–" : this.t(d.cloud_status ? "stat.cloud_on" : "stat.cloud_off"))}
      </div>
      <div class="card">
        <gp-port-grid .ports=${d.ports} .selected=${this._port} @port-select=${(e: CustomEvent<number>) => (this._port = e.detail)}></gp-port-grid>
      </div>
      <div class="card detail">${port ? this._portDetail(d, port) : html`<span class="note">${this.t("port.hint")}</span>`}</div>
      <gp-confirm
        ?open=${this._pending !== null}
        .heading=${this.t("confirm.title")}
        .message=${this._pending?.message ?? ""}
        .okLabel=${this.t("confirm.ok")}
        .cancelLabel=${this.t("confirm.cancel")}
        @cancel=${() => (this._pending = null)}
        @confirm=${() => {
          const run = this._pending?.run;
          this._pending = null;
          run?.();
        }}
      ></gp-confirm>
    `;
  }

  private _stat(key: string, value: string) {
    return html`<div class="card stat"><div class="label">${this.t(key)}</div><div class="value">${value}</div></div>`;
  }

  private _choose(id: string): void {
    this._port = null;
    this.fire("select-device", id);
  }

  private _portDetail(d: DeviceInfo, p: PortInfo) {
    const w = (request: { action: string; value?: boolean | number | string; confirm?: boolean }) =>
      this.write(d.entry_id, { ...request, index: p.index });
    const canWrite = this.admin && p.is_poe;
    // keep the limit inputs while the user types, reset them when another port is shown
    if (this._limitPort !== p.index) {
      this._limitPort = p.index;
      this._limitUp = String(p.limit_up_mbps ?? 0);
      this._limitDown = String(p.limit_down_mbps ?? 0);
    }
    return html`
      <h2>${this.t("port.title", { port: p.label })}</h2>
      <div class="metrics">
        <div><div class="label">${this.t("port.link")}</div><div class="value">${p.connected ? speed(p.speed_mbps) : this.t("port.no_link")}</div></div>
        ${p.is_poe ? html`<div><div class="label">${this.t("port.power")}</div><div class="value">${watts(p.power_w)}</div></div>` : nothing}
        <div><div class="label">${this.t("port.tx")}</div><div class="value">${rate(p.tx_kbps)}</div></div>
        <div><div class="label">${this.t("port.rx")}</div><div class="value">${rate(p.rx_kbps)}</div></div>
      </div>
      ${!p.is_poe ? html`<p class="note">${this.t("port.uplink_note")}</p>` : nothing}
      ${p.is_poe && !this.admin ? html`<p class="note">${this.t("admin.required")}</p>` : nothing}
      ${p.is_poe
        ? html`
            <div class="row">
              <span>${this.t("port.poe")}</span>
              <gp-toggle
                .checked=${p.poe_enabled === true}
                ?disabled=${!canWrite}
                @toggle=${(e: CustomEvent<boolean>) =>
                  e.detail
                    ? w({ action: "poe", value: true })
                    : this._ask(this.t("confirm.poe_off", { port: p.label }), () => w({ action: "poe", value: false }))}
              ></gp-toggle>
            </div>
            <div class="row">
              <span>${this.t("port.extend")}</span>
              <gp-toggle
                .checked=${p.phy_mode === "10m_half" || p.phy_mode === "10m_full"}
                ?disabled=${!canWrite}
                @toggle=${(e: CustomEvent<boolean>) => w({ action: "extend", value: e.detail })}
              ></gp-toggle>
            </div>
            <div class="row">
              <span>${this.t("port.mode")}</span>
              <select ?disabled=${!canWrite} .value=${p.phy_mode ?? ""} @change=${(e: Event) => w({ action: "mode", value: (e.target as HTMLSelectElement).value })}>
                ${MODES.map((m) => html`<option value=${m} ?selected=${p.phy_mode === m}>${this.t(`mode.${m}`)}</option>`)}
              </select>
            </div>
            <div class="row">
              <span>${this.t("port.priority")}</span>
              <select ?disabled=${!canWrite} @change=${(e: Event) => w({ action: "priority", value: Number((e.target as HTMLSelectElement).value) })}>
                ${[0, 1, 2, 3, 4, 5, 6].map((n) => html`<option value=${n} ?selected=${p.priority === n}>${n}</option>`)}
              </select>
            </div>
            <div class="row">
              <span>${this.t("port.limit_up")}</span>
              <span class="limit">
                <input type="number" min="0" max="1000" .value=${this._limitUp} ?disabled=${!canWrite} @input=${(e: Event) => (this._limitUp = (e.target as HTMLInputElement).value)} />
                <button class="btn" ?disabled=${!canWrite} @click=${() => w({ action: "limit_up", value: Number(this._limitUp) })}>${this.t("port.apply")}</button>
              </span>
            </div>
            <div class="row">
              <span>${this.t("port.limit_down")}</span>
              <span class="limit">
                <input type="number" min="0" max="1000" .value=${this._limitDown} ?disabled=${!canWrite} @input=${(e: Event) => (this._limitDown = (e.target as HTMLInputElement).value)} />
                <button class="btn" ?disabled=${!canWrite} @click=${() => w({ action: "limit_down", value: Number(this._limitDown) })}>${this.t("port.apply")}</button>
              </span>
            </div>
            <div class="row">
              <span>${this.t("port.flow")}</span>
              <gp-toggle .checked=${p.flow_control === true} ?disabled=${!canWrite} @toggle=${(e: CustomEvent<boolean>) => w({ action: "flow", value: e.detail })}></gp-toggle>
            </div>
            <div class="row">
              <span></span>
              <button class="btn danger" ?disabled=${!canWrite} @click=${() => this._ask(this.t("confirm.restart_port", { port: p.label }), () => w({ action: "restart_port" }))}>${this.t("port.restart")}</button>
            </div>
          `
        : nothing}
    `;
  }

  private _ask(message: string, run: () => void): void {
    this._pending = { message, run };
  }
}
