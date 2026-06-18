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
  });
  it('formats a valid ISO date', () => {
    expect(formatDate('2026-01-15T10:00:00')).not.toBe('');
  });
});
