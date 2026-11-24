import { LitElement, css, html } from "lit";
import { property } from "lit/decorators.js";
import { customElement } from "../define";

/** Modal confirmation. Fires `confirm` or `cancel`. */
@customElement("gp-confirm")
export class GpConfirm extends LitElement {
  @property({ type: Boolean, reflect: true }) open = false;
  @property() heading = "";
  @property() message = "";
  @property() okLabel = "OK";
  @property() cancelLabel = "Cancel";

  static styles = css`
    :host {
      display: none;
    }
    :host([open]) {
      display: flex;
      position: fixed;
      inset: 0;
      z-index: 20;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.55);
      padding: 16px;
    }
    .dialog {
      max-width: 420px;
      width: 100%;
      background: var(--gp-surface, #0b131d);
      color: var(--gp-fg, #dff2f6);
      border: 1px solid var(--gp-warn, #ffb020);
      border-radius: 12px;
      padding: 20px;
      font-family: var(--gp-sans, system-ui);
    }
    h3 {
      margin: 0 0 8px;
      color: var(--gp-warn, #ffb020);
    }
    p {
      margin: 0 0 18px;
      line-height: 1.5;
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
    button {
      font: inherit;
      color: inherit;
      border-radius: 8px;
      padding: 7px 16px;
      border: 1px solid var(--gp-line, #1b2b3d);
      background: var(--gp-surface-2, #101b28);
      cursor: pointer;
    }
    button.ok {
      background: var(--gp-crit, #ff4d5e);
      border-color: var(--gp-crit, #ff4d5e);
      color: #fff;
    }
  `;

  render() {
    return html`<div class="dialog" role="alertdialog" aria-modal="true">
      <h3>${this.heading}</h3>
      <p>${this.message}</p>
      <div class="actions">
        <button @click=${() => this.dispatchEvent(new CustomEvent("cancel"))}>${this.cancelLabel}</button>
        <button class="ok" @click=${() => this.dispatchEvent(new CustomEvent("confirm"))}>${this.okLabel}</button>
      </div>
    </div>`;
  }
}
