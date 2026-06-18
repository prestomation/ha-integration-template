// Locale tables, statically imported so Rollup inlines them into the IIFE bundle
// (no runtime fetch; works offline). English is the source of truth and the
// fallback; every other table is parity-checked against it in tests (i18n.test.js).
//
// To add a locale: drop `<lang>.json` next to en.json, import it here, and add
// it to LOCALES. The parity test will then require full key coverage.
import en from './en.json';
import de from './de.json';

export const DEFAULT_LOCALE = 'en';

export const LOCALES: Record<string, Record<string, string>> = {
  en,
  de,
};
