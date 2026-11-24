import { css } from "lit";

/** Default scheme (Reactor). Other schemes are applied from palettes.ts as inline custom properties. */
export const themeStyles = css`
  :host {
    --gp-bg: #05090f;
    --gp-surface: #0b131d;
    --gp-surface-2: #101b28;
    --gp-inset: #0d1723;
    --gp-line: #1b2b3d;
    --gp-line-soft: #152435;
    --gp-fg: #dff2f6;
    --gp-fg-2: #9fb8c6;
    --gp-dim: #5d7d92;
    --gp-accent: #2ae6dc;
    --gp-accent-deep: #1b8fd6;
    --gp-accent-wash: #0e2b30;
    --gp-magenta: #ff3ea5;
    --gp-magenta-wash: #2a0d1e;
    --gp-ok: #35d67a;
    --gp-warn: #ffb020;
    --gp-crit: #ff4d5e;
    --gp-track: #132434;
    --gp-on-accent: #04141a;
  }
  :host([light]) {
    --gp-bg: #eef2f6;
    --gp-surface: #ffffff;
    --gp-surface-2: #f6f9fb;
    --gp-inset: #e8eef3;
    --gp-line: #cbd8e2;
    --gp-line-soft: #dfe7ee;
    --gp-fg: #0c1a24;
    --gp-fg-2: #3a5162;
    --gp-dim: #5b7484;
    --gp-accent: #0c847e;
    --gp-accent-deep: #0f5f8c;
    --gp-accent-wash: #d9f0ee;
    --gp-magenta: #b4176e;
    --gp-magenta-wash: #fbe4f0;
    --gp-ok: #0f7a44;
    --gp-warn: #8a5804;
    --gp-crit: #b52436;
    --gp-track: #dae3ea;
    --gp-on-accent: #ffffff;
  }
`;

export const baseStyles = css`
  :host {
    --gp-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    --gp-sans: var(--paper-font-body1_-_font-family, "Roboto", system-ui, -apple-system, sans-serif);
    display: block;
    color: var(--gp-fg);
    font-family: var(--gp-sans);
    font-size: 15px;
    line-height: 1.5;
  }
  * {
    box-sizing: border-box;
  }
  .card {
    background: var(--gp-surface);
    border: 1px solid var(--gp-line);
    border-radius: 10px;
    padding: 16px 18px;
  }
  .label {
    font-family: var(--gp-mono);
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--gp-dim);
  }
  .value {
    font-family: var(--gp-mono);
    font-variant-numeric: tabular-nums;
    font-weight: 600;
  }
  .grid {
    display: grid;
    gap: 12px;
  }
  .grid > * {
    min-width: 0;
  }
  h2 {
    margin: 0 0 12px;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  button {
    font: inherit;
    color: inherit;
  }
  .btn {
    background: var(--gp-surface-2);
    border: 1px solid var(--gp-line);
    border-radius: 8px;
    padding: 7px 14px;
    cursor: pointer;
  }
  .btn:hover:not(:disabled) {
    border-color: var(--gp-accent);
  }
  .btn.primary {
    background: var(--gp-accent);
    border-color: var(--gp-accent);
    color: var(--gp-on-accent);
  }
  .btn.danger {
    border-color: var(--gp-crit);
    color: var(--gp-crit);
  }
  .btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
  select,
  input[type="number"] {
    font: inherit;
    color: var(--gp-fg);
    background: var(--gp-inset);
    border: 1px solid var(--gp-line);
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 0;
  }
  select:disabled,
  input:disabled {
    opacity: 0.5;
  }
  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 9px 0;
    border-top: 1px solid var(--gp-line-soft);
  }
  .row:first-of-type {
    border-top: none;
  }
  .pill {
    font-family: var(--gp-mono);
    font-size: 10.5px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid var(--gp-line);
    color: var(--gp-dim);
  }
  .pill.ok {
    color: var(--gp-ok);
    border-color: var(--gp-ok);
  }
  .pill.bad {
    color: var(--gp-crit);
    border-color: var(--gp-crit);
  }
  .note {
    color: var(--gp-dim);
    font-size: 13px;
  }
`;
