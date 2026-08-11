import { afterEach, describe, expect, it } from 'vitest';
import { setLanguage, t, tn } from '../src/i18n.ts';
import { DEFAULT_LOCALE, LOCALES } from '../src/locales/index.ts';

// Behavioural tests for the i18n module. The locale parity / key-usage gates
// live in `i18n-parity.test.js` — they analyse `src/*.ts` as *text* read off
// disk, which is a different kind of test (and one mutation testing has to skip;
// see `vitest.stryker.config.js`).

// The i18n module holds global state; reset to the default after every test.
afterEach(() => setLanguage(DEFAULT_LOCALE));

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
