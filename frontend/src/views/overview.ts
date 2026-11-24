import { css, html } from "lit";
import { property } from "lit/decorators.js";
import { customElement } from "../define";
import { watts } from "../format";
import type { DeviceInfo } from "../types";
import { baseStyles } from "../styles";
import "../components/gp-port-grid";
import { ViewBase } from "./view-base";

@customElement("gp-overview")
export class GpOverview extends ViewBase {
  @property({ attribute: false }) devices: DeviceInfo[] = [];

  static styles = [
    baseStyles,
    css`
      .summary {
        display: flex;
        gap: 28px;
        flex-wrap: wrap;
        margin-bottom: 14px;
      }
      .big {
        font-size: 26px;
      }
      .cards {
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      }
      .card {
        cursor: pointer;
      }
      .card:hover {
        border-color: var(--gp-accent);
      }
      .head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 10px;
      }
      .title {
        font-weight: 600;
      }
      .metrics {
        display: flex;
        gap: 22px;
        margin: 10px 0;
      }
    `,
  ];

  render() {
    if (!this.devices.length) return html`<div class="card note">${this.t("overview.empty")}</div>`;
    const total = this.devices.reduce((sum, d) => sum + (d.total_power_w ?? 0), 0);
    return html`
      <div class="summary">
        <div>
          <div class="label">${this.t("overview.total_power")}</div>
          <div class="value big">${watts(total)}</div>
        </div>
        <div>
          <div class="label">${this.t("overview.switches")}</div>
          <div class="value big">${this.devices.length}</div>
        </div>
      </div>
      <div class="grid cards">${this.devices.map((d) => this._card(d))}</div>
    `;
  }

  private _card(d: DeviceInfo) {
    const linked = d.ports.filter((p) => p.connected).length;
    return html`<div class="card" @click=${() => this.fire("open-device", d.entry_id)}>
      <div class="head">
        <div>
          <div class="title">${d.title}</div>
          <div class="note">${d.model ?? ""} ${d.firmware}</div>
        </div>
        <span class="pill ${d.available ? "ok" : "bad"}">${this.t(d.available ? "state.online" : "state.offline")}</span>
      </div>
      <div class="metrics">
        <div>
          <div class="label">${this.t("stat.power")}</div>
          <div class="value">${watts(d.total_power_w)}</div>
        </div>
        <div>
          <div class="label">${this.t("stat.temperature")}</div>
          <div class="value">${d.temperature_c === null ? "–" : `${d.temperature_c.toFixed(1)} °C`}</div>
        </div>
      </div>
      <gp-port-grid compact .ports=${d.ports}></gp-port-grid>
      <div class="note" style="margin-top:8px">${this.t("overview.ports_linked", { n: linked, m: d.ports.length })}</div>
    </div>`;
  }
}
