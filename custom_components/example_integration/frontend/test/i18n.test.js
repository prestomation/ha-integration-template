import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { setLanguage, t, tn } from '../src/i18n.ts';
import { DEFAULT_LOCALE, LOCALES } from '../src/locales/index.ts';

// The i18n module holds global state; reset to the default after every test.
afterEach(() => setLanguage(DEFAULT_LOCALE));

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

describe('t() / tn()', () => {
  it('looks up a key in the active locale', () => {
    setLanguage('en');
    expect(t('panel.title')).toBe('Example Integration');
    setLanguage('de');
    expect(t('panel.title')).toBe(LOCALES.de['panel.title']);
  });

  it('interpolates {param} tokens', () => {
    setLanguage('en');
    expect(t('panel.created')).toBe('Created');
  });

  it('falls back to the key when missing', () => {
    setLanguage('en');
    expect(t('does.not.exist')).toBe('does.not.exist');
  });

  it('selects plural categories', () => {
    setLanguage('en');
    expect(tn('count', 1)).toBe('1 item');
    expect(tn('count', 3)).toBe('3 items');
  });
});

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
