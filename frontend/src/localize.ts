/** Panel translations: English is bundled as the fallback, other languages are separate chunks loaded on demand. */

import { en } from "./locales/en";

export type Strings = Record<string, string>;

const LOADERS: Record<string, () => Promise<Strings>> = {
  de: () => import("./locales/de").then((m) => m.de),
};

export const AVAILABLE_LANGUAGES = ["en", ...Object.keys(LOADERS)].sort();

const loaded: Record<string, Strings> = { en };

const base = (language: string): string => (language || "en").split("-")[0].toLowerCase();

export async function loadCatalogue(language: string): Promise<Strings> {
  const code = base(language);
  if (loaded[code]) return loaded[code];
  const loader = LOADERS[code];
  if (!loader) return en;
  try {
    loaded[code] = await loader();
    return loaded[code];
  } catch {
    return en;
  }
}

/** Look up a key, falling back to English and then to the key itself. {name} placeholders are replaced. */
export function translate(catalogue: Strings, key: string, values?: Record<string, string | number>): string {
  let text = catalogue[key] ?? en[key] ?? key;
  if (values) for (const [name, value] of Object.entries(values)) text = text.replace(`{${name}}`, String(value));
  return text;
}
