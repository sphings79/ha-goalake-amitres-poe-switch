import { LitElement, css, html } from "lit";
import { property } from "lit/decorators.js";
import { customElement } from "../define";

/** A small switch. Fires `toggle` with the requested state; the owner decides whether to apply it. */
@customElement("gp-toggle")
export class GpToggle extends LitElement {
  @property({ type: Boolean }) checked = false;
  @property({ type: Boolean }) disabled = false;

  static styles = css`
    button {
      width: 42px;
      height: 24px;
      border-radius: 999px;
      border: 1px solid var(--gp-line, #1b2b3d);
      background: var(--gp-track, #132434);
      position: relative;
      cursor: pointer;
      padding: 0;
      transition: background 0.15s;
    }
    button[aria-checked="true"] {
      background: var(--gp-accent, #2ae6dc);
      border-color: var(--gp-accent, #2ae6dc);
    }
    button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    span {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: var(--gp-fg, #dff2f6);
      transition: transform 0.15s;
    }
    button[aria-checked="true"] span {
      transform: translateX(18px);
      background: var(--gp-on-accent, #04141a);
    }
  `;

  render() {
    return html`<button
      role="switch"
      aria-checked=${this.checked ? "true" : "false"}
      ?disabled=${this.disabled}
      @click=${() => this.dispatchEvent(new CustomEvent("toggle", { detail: !this.checked }))}
    >
      <span></span>
    </button>`;
  }
}
