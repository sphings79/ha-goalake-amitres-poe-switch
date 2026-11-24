import { LitElement } from "lit";
import { property } from "lit/decorators.js";
import type { WriteRequest } from "../types";

export type Translate = (key: string, values?: Record<string, string | number>) => string;

/** Shared properties and event helpers of the three views. */
export class ViewBase extends LitElement {
  @property({ attribute: false }) t: Translate = (k) => k;
  @property({ type: Boolean }) admin = false;

  protected fire<T>(name: string, detail: T): void {
    this.dispatchEvent(new CustomEvent(name, { detail, bubbles: true, composed: true }));
  }

  protected write(entryId: string, request: WriteRequest): void {
    this.fire("write", { entry_id: entryId, request });
  }
}
