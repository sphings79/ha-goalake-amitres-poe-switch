import { LitElement, css, html } from "lit";
import { property } from "lit/decorators.js";
import { customElement } from "../define";
import { watts } from "../format";
import type { PortInfo } from "../types";

/** Front view of the switch: PoE ports 1..n, then the uplinks. Fires `port-select` with the array index. */
@customElement("gp-port-grid")
export class GpPortGrid extends LitElement {
  @property({ attribute: false }) ports: PortInfo[] = [];
  @property({ type: Number }) selected: number | null = null;
  @property({ type: Boolean }) compact = false;
  @property({ type: Boolean, reflect: true }) readonly = false;

  static styles = css`
    :host {
      display: block;
    }
    .rack {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: stretch;
    }
    .gap {
      width: 10px;
    }
    button.port {
      font: inherit;
      color: var(--gp-fg, #dff2f6);
      background: var(--gp-inset, #0d1723);
      border: 1px solid var(--gp-line, #1b2b3d);
      border-radius: 8px;
      min-width: 56px;
      padding: 8px 4px 7px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      position: relative;
    }
    :host([compact]) button.port {
      min-width: 0;
      width: 21px;
      height: 21px;
      padding: 0;
      border-radius: 5px;
    }
    button.port:hover {
      border-color: var(--gp-accent, #2ae6dc);
    }
    :host([readonly]) button.port {
      cursor: default;
    }
    :host([readonly]) button.port:hover:not(.selected) {
      border-color: var(--gp-line, #1b2b3d);
    }
    button.port.selected {
      border-color: var(--gp-accent, #2ae6dc);
      box-shadow: 0 0 0 1px var(--gp-accent, #2ae6dc);
    }
    .led {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--gp-track, #132434);
    }
    .linked .led {
      background: var(--gp-ok, #35d67a);
      box-shadow: 0 0 6px var(--gp-ok, #35d67a);
    }
    .poe-on .led {
      background: var(--gp-accent, #2ae6dc);
      box-shadow: 0 0 6px var(--gp-accent, #2ae6dc);
    }
    .poe-off {
      border-style: dashed !important;
      border-color: var(--gp-crit, #ff4d5e) !important;
    }
    .num {
      font-family: var(--gp-mono, monospace);
      font-weight: 600;
      font-size: 13px;
    }
    .sub {
      font-family: var(--gp-mono, monospace);
      font-size: 10px;
      color: var(--gp-dim, #5d7d92);
      min-height: 13px;
    }
    :host([compact]) .num,
    :host([compact]) .sub {
      display: none;
    }
    :host([compact]) .led {
      margin: auto;
    }
  `;

  private _ordered(): PortInfo[] {
    const poe = this.ports.filter((p) => p.is_poe).sort((a, b) => Number(a.label) - Number(b.label));
    const up = this.ports.filter((p) => !p.is_poe).sort((a, b) => a.label.localeCompare(b.label));
    return [...poe, ...up];
  }

  render() {
    const ordered = this._ordered();
    const firstUplink = ordered.findIndex((p) => !p.is_poe);
    return html`<div class="rack">
      ${ordered.map(
        (p, i) => html`${i === firstUplink && i > 0 ? html`<span class="gap"></span>` : ""}
          <button
            class="port ${p.connected ? "linked" : ""} ${p.is_poe && p.power_w ? "poe-on" : ""} ${p.is_poe && p.poe_enabled === false ? "poe-off" : ""} ${this.selected === p.index ? "selected" : ""}"
            title="${p.label}"
            @click=${() => !this.readonly && this.dispatchEvent(new CustomEvent("port-select", { detail: p.index }))}
          >
            <span class="led"></span>
            <span class="num">${p.label}</span>
            <span class="sub">${p.is_poe ? (p.power_w ? watts(p.power_w) : "") : p.connected ? `${p.speed_mbps}M` : ""}</span>
          </button>`,
      )}
    </div>`;
  }
}
