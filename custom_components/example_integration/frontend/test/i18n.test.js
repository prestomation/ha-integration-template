import { afterEach, describe, expect, it } from 'vitest';
import { getLanguage, setLanguage, t, tn } from '../src/i18n.ts';
import { DEFAULT_LOCALE, LOCALES } from '../src/locales/index.ts';

// Behavioural tests for the i18n module. The translation-quality gates (locale
// parity, untranslated leaks, key usage) live in `i18n-parity.test.js` — they
// analyse `src/*.ts` as *text* read off disk, which is a different kind of test,
// and one the mutation run has to skip (see `vitest.stryker.config.js`).

// The i18n module holds global state; reset to the default after every test.
afterEach(() => setLanguage(DEFAULT_LOCALE));

/**
 * Run `body` with extra keys temporarily present in a locale table.
 *
 * The bundled tables are deliberately at full parity (i18n-parity.test.js is a
 * gate), which makes several real code paths — the per-key English fallback,
 * multi-character interpolation tokens — unreachable with the shipped data.
 * They are not dead code: they are what a fork mid-translation relies on. This
 * stages that state and always tears it back down.
 */
function withKeys(keys, body, locale = DEFAULT_LOCALE) {
  const table = LOCALES[locale];
  for (const [key, value] of Object.entries(keys)) table[key] = value;
  try {
    body();
  } finally {
    for (const key of Object.keys(keys)) delete table[key];
  }
}

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

describe('setLanguage() locale resolution', () => {
  it('matches a bundled tag exactly', () => {
    setLanguage('de');
    expect(getLanguage()).toBe('de');
    expect(t('panel.title')).toBe(LOCALES.de['panel.title']);
  });

  // HA reports the user's language as whatever the browser/profile says, so
  // "DE", "de-AT" and "de-CH" all have to land on the bundled `de` table.
  it('matches case-insensitively', () => {
    setLanguage('DE');
    expect(getLanguage()).toBe('de');
    expect(t('panel.title')).toBe(LOCALES.de['panel.title']);
  });

  it('falls back from a regional tag to its base language', () => {
    setLanguage('de-AT');
    expect(getLanguage()).toBe('de');
    expect(t('panel.title')).toBe(LOCALES.de['panel.title']);
  });

  it('matches a regional tag case-insensitively too', () => {
    setLanguage('DE-ch');
    expect(getLanguage()).toBe('de');
  });

  it('falls back to the default for an unbundled language', () => {
    setLanguage('xx-YY');
    expect(getLanguage()).toBe(DEFAULT_LOCALE);
    expect(t('panel.title')).toBe(LOCALES[DEFAULT_LOCALE]['panel.title']);
  });

  it('falls back to the default for an empty language', () => {
    setLanguage('de');
    setLanguage(undefined);
    expect(getLanguage()).toBe(DEFAULT_LOCALE);
    setLanguage('de');
    setLanguage('');
    expect(getLanguage()).toBe(DEFAULT_LOCALE);
  });
});

describe('t() interpolation', () => {
  it('leaves the template alone when no params are given', () => {
    setLanguage('en');
    // `count.one` carries an `{n}` token; called without params the placeholder
    // must survive untouched rather than being resolved against nothing.
    expect(t('count.one')).toBe('{n} item');
  });

  it('leaves a placeholder intact when the param is absent or null', () => {
    setLanguage('en');
    expect(t('count.one', { other: 1 })).toBe('{n} item');
    expect(t('count.one', { n: null })).toBe('{n} item');
    expect(t('count.one', { n: undefined })).toBe('{n} item');
  });

  it('substitutes falsy-but-present values', () => {
    setLanguage('en');
    // 0 and '' are legitimate values; only null/undefined mean "not supplied".
    expect(t('count.one', { n: 0 })).toBe('0 item');
    expect(t('count.one', { n: '' })).toBe(' item');
  });

  it('interpolates multi-character token names', () => {
    // Every bundled token happens to be the single character `{n}`, so a
    // pattern of `\{(\w)\}` would pass on the real tables while silently
    // failing the moment a fork adds `{count}` or `{date}`.
    withKeys({ 'tmp.multi': 'due {date} for {itemName}' }, () => {
      setLanguage('en');
      expect(t('tmp.multi', { date: '2030-01-01', itemName: 'Shelf' })).toBe(
        'due 2030-01-01 for Shelf',
      );
    });
  });
});

describe('tn() key fallback chain', () => {
  // The chain is `current[key.cat] ?? current[key.other] ?? fallback[key.cat]
  // ?? fallback[key.other] ?? key`. Its middle rungs are unreachable with the
  // real tables *by design* — i18n-parity.test.js enforces full key parity
  // across locales, so `current` is never missing what `fallback` has. They
  // exist for a fork mid-translation, which is exactly the state these tests
  // stage explicitly.

  it('falls back to .other within the active locale', () => {
    // The key goes into the *German* table, so the chain stops at
    // `current[key.other]` and never reaches the English rungs below it.
    withKeys(
      { 'tmp.cat.other': '{n} andere' },
      () => {
        setLanguage('de');
        // German selects "one" for 1; only `.other` is defined here.
        expect(tn('tmp.cat', 1)).toBe('1 andere');
      },
      'de',
    );
  });

  it('falls back to the English category key when the locale has neither', () => {
    withKeys({ 'tmp.en.one': '{n} english thing' }, () => {
      setLanguage('de');
      expect(tn('tmp.en', 1)).toBe('1 english thing');
    });
  });

  it('falls back to the English .other when nothing else matches', () => {
    withKeys({ 'tmp.enother.other': '{n} english things' }, () => {
      setLanguage('de');
      expect(tn('tmp.enother', 3)).toBe('3 english things');
    });
  });
});

describe('tn() counting', () => {
  it('exposes the count as {n} by default', () => {
    setLanguage('en');
    expect(tn('count', 5)).toBe('5 items');
  });

  it('lets params override the count', () => {
    setLanguage('en');
    expect(tn('count', 5, { n: 'many' })).toBe('many items');
  });

  it('falls back to .other when the category key is absent', () => {
    setLanguage('en');
    // English selects "one" for 1 and "other" for everything else; a category
    // with no key of its own must land on `.other` rather than the raw key.
    expect(tn('count', 0)).toBe('0 items');
  });

  it('falls back to the raw key when nothing matches', () => {
    setLanguage('en');
    expect(tn('no.such.key', 2)).toBe('no.such.key');
  });

});
