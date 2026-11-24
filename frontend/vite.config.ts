import { defineConfig } from "vite";

// The build output is committed: HACS does not run a build step.
export default defineConfig({
  build: {
    outDir: "../custom_components/goalake_poe_switch/frontend",
    emptyOutDir: true,
    target: "es2021",
    minify: "esbuild",
    sourcemap: false,
    rollupOptions: {
      input: {
        "goalake-poe-switch-panel": "src/panel.ts",
        "goalake-poe-switch-card": "src/card.ts",
      },
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: (chunk) => {
          const locale = chunk.facadeModuleId?.match(/[\\/]locales[\\/]([a-z]{2})\.ts$/)?.[1];
          return locale ? `goalake-poe-switch-lang-${locale}.js` : "goalake-poe-switch-shared.js";
        },
        format: "es",
      },
    },
  },
});
