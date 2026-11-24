/** Like Lit's `@customElement`, but a name that is already taken is left alone (a second bundle load must not throw). */
export function customElement(name: string) {
  return (element: CustomElementConstructor) => {
    if (!customElements.get(name)) customElements.define(name, element);
  };
}
