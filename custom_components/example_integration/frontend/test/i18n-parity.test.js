import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { DEFAULT_LOCALE, LOCALES } from '../src/locales/index.ts';

// Translation quality gates: locale key/placeholder parity, untranslated leaks,
// and key usage. The last of these reads `src/*.ts` off disk and analyses it as
// text, so this file is deliberately kept separate from the behavioural
// `i18n.test.js` and is excluded from the mutation-testing run — under Stryker
// it would be reading *mutated* source and reporting bogus kills. See
// `vitest.stryker.config.js`.

// Strings allowed to be byte-identical to English in every locale (product
// name, symbols, bare-placeholder passthroughs). Keep tiny.
const INTENTIONALLY_IDENTICAL = new Set(['panel.name']); // "Name" is identical in de

// Per-locale reviewed cognates/loanwords that are genuinely identical.
const COGNATE_IDENTICAL = {
  de: [],
};

const EN = LOCALES[DEFAULT_LOCALE];
const OTHER_LOCALES = Object.keys(LOCALES).filter((l) => l !== DEFAULT_LOCALE);

// Tokens like {n} or {date} inside a string, as a sorted set.
const placeholders = (s) =>
  [...new Set([...String(s).matchAll(/\{(\w+)\}/g)].map((m) => m[1]))].sort();

// Concatenate all frontend TS sources for static key-usage analysis.
const SRC = (() => {
  const rel = 'custom_components/example_integration/frontend/src';
  const dir = existsSync(resolve(process.cwd(), rel))
    ? resolve(process.cwd(), rel)
    : resolve(process.cwd(), 'src');
  return readdirSync(dir)
    .filter((f) => f.endsWith('.ts'))
    .map((f) => readFileSync(`${dir}/${f}`, 'utf8'))
    .join('\n');
})();

const literalKeys = (fn) =>
  [...SRC.matchAll(new RegExp(`\\b${fn}\\(\\s*['"]([^'"]+)['"]\\s*[),]`, 'g'))].map((m) => m[1]);
const T_KEYS = [...new Set(literalKeys('t'))];
const TN_KEYS = [...new Set(literalKeys('tn'))];

describe.each(OTHER_LOCALES)('locale "%s"', (locale) => {
  const table = LOCALES[locale];
  const cognates = new Set(COGNATE_IDENTICAL[locale] || []);

  it('has exact key parity with English', () => {
    expect(Object.keys(table).sort()).toEqual(Object.keys(EN).sort());
  });

  it('has matching placeholder sets per key', () => {
    for (const key of Object.keys(EN)) {
      expect(placeholders(table[key]), `placeholders for ${key}`).toEqual(
        placeholders(EN[key]),
      );
    }
  });

  it('has no untranslated leaks (value identical to English)', () => {
    for (const key of Object.keys(EN)) {
      if (INTENTIONALLY_IDENTICAL.has(key) || cognates.has(key)) continue;
      expect(table[key], `"${key}" is identical to English`).not.toBe(EN[key]);
    }
  });
});

describe('key usage', () => {
  it('every t() key exists in the English source', () => {
    for (const key of T_KEYS) {
      expect(EN, `t('${key}')`).toHaveProperty(key);
    }
  });

  it('every tn() base has an .other plural form', () => {
    for (const key of TN_KEYS) {
      expect(EN, `tn('${key}') base`).toHaveProperty(`${key}.other`);
    }
  });

  it('has no unused English keys', () => {
    const pluralBases = new Set(
      Object.keys(EN)
        .map((k) => k.match(/^(.*)\.(one|two|few|many|zero|other)$/))
        .filter(Boolean)
        .map((m) => m[1]),
    );
    const used = new Set([...T_KEYS, ...TN_KEYS]);
    for (const key of Object.keys(EN)) {
      const base = key.replace(/\.(one|two|few|many|zero|other)$/, '');
      const isUsed = used.has(key) || used.has(base) || pluralBases.has(base) && used.has(base);
      expect(isUsed, `unused key "${key}"`).toBe(true);
    }
  });
});
