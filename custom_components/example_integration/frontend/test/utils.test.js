import { describe, it, expect } from 'vitest';
import { escapeHTML, parseRoute, buildPath, formatDate } from '../src/utils.ts';

describe('escapeHTML', () => {
  it('escapes HTML-significant characters', () => {
    expect(escapeHTML('<b>"x" & \'y\'</b>')).toBe(
      '&lt;b&gt;&quot;x&quot; &amp; &#39;y&#39;&lt;/b&gt;',
    );
  });
  it('handles null/undefined', () => {
    expect(escapeHTML(null)).toBe('');
    expect(escapeHTML(undefined)).toBe('');
  });
});

describe('parseRoute / buildPath', () => {
  it('parses the list route', () => {
    expect(parseRoute({ prefix: '/example-integration', path: '/' })).toEqual({
      view: 'list',
      detailId: null,
    });
    expect(parseRoute(undefined)).toEqual({ view: 'list', detailId: null });
  });

  it('parses an item detail route', () => {
    expect(parseRoute({ prefix: '/example-integration', path: '/items/abc123' })).toEqual({
      view: 'list',
      detailId: 'abc123',
    });
  });

  it('falls back to the list for unknown paths', () => {
    expect(parseRoute({ prefix: '/x', path: '/nope/zzz' })).toEqual({
      view: 'list',
      detailId: null,
    });
  });

  // HA hands the panel whatever is in the address bar, and a doubled slash from
  // a hand-edited URL or a concatenated prefix is ordinary. Trimming only *one*
  // slash from each end would leave an empty leading segment, pushing 'items'
  // to parts[1] and losing the detail id.
  it('tolerates repeated leading and trailing slashes', () => {
    for (const path of ['//items/abc123', '/items/abc123//', '///items/abc123///']) {
      expect(parseRoute({ prefix: '/p', path })).toEqual({
        view: 'list',
        detailId: 'abc123',
      });
    }
  });

  it('builds the list path as a bare slash', () => {
    // The round-trip test can't see this: parseRoute('') and parseRoute('/')
    // both parse to the list, so an empty string would round-trip just fine
    // while producing a href the browser resolves against the wrong base.
    expect(buildPath({ view: 'list', detailId: null })).toBe('/');
  });

  it('round-trips losslessly', () => {
    for (const state of [
      { view: 'list', detailId: null },
      { view: 'list', detailId: 'abc123' },
    ]) {
      expect(parseRoute({ prefix: '/p', path: buildPath(state) })).toEqual(state);
    }
  });

  it('encodes ids with special characters', () => {
    const state = { view: 'list', detailId: 'a/b c' };
    const path = buildPath(state);
    expect(path).toBe('/items/a%2Fb%20c');
    expect(parseRoute({ prefix: '/p', path })).toEqual(state);
  });
});

describe('formatDate', () => {
  it('returns empty string for missing/invalid input', () => {
    expect(formatDate(undefined)).toBe('');
    expect(formatDate('not-a-date')).toBe('');
    expect(formatDate('')).toBe('');
  });

  // `new Date(null)` is the Unix epoch, not an invalid date — without the
  // explicit falsy guard a missing timestamp renders as 1/1/1970 rather than
  // blank. Storage round-trips through JSON, so a null is entirely reachable.
  it('returns empty string for a null timestamp rather than the epoch', () => {
    expect(formatDate(null)).toBe('');
  });

  it('formats a valid ISO date', () => {
    expect(formatDate('2026-01-15T10:00:00')).not.toBe('');
  });
});
