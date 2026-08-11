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

  it('coerces non-strings before escaping', () => {
    // Item values arrive from JSON, so numbers and objects reach this function.
    expect(escapeHTML(42)).toBe('42');
    expect(escapeHTML(0)).toBe('0');
    expect(escapeHTML(false)).toBe('false');
    expect(escapeHTML(['<x>'])).toBe('&lt;x&gt;');
  });

  it('escapes the ampersand first, so entities are not double-decodable', () => {
    // If `&` were escaped last, `&lt;` in the input would come out as a literal
    // `&lt;` that the browser renders as `<` — an escape that un-escapes.
    expect(escapeHTML('&lt;script&gt;')).toBe('&amp;lt;script&amp;gt;');
    expect(escapeHTML('&amp;')).toBe('&amp;amp;');
  });

  // This function is the XSS boundary for the whole panel: every user string
  // reaches innerHTML through it. Assert on the payloads that matter, not just
  // on the character set.
  describe('injection payloads', () => {
    const neutered = (payload) => {
      const escaped = escapeHTML(payload);
      // Nothing that can open a tag or close an attribute may survive.
      expect(escaped).not.toMatch(/[<>"']/);
      return escaped;
    };

    it('neuters a script tag', () => {
      expect(neutered('<script>alert(1)</script>')).toBe(
        '&lt;script&gt;alert(1)&lt;/script&gt;',
      );
    });

    it('neuters an inline event handler', () => {
      expect(neutered('<img src=x onerror=alert(1)>')).toBe(
        '&lt;img src=x onerror=alert(1)&gt;',
      );
    });

    it('neuters an attribute-breakout payload', () => {
      // The panel interpolates into attributes as well as text nodes, so the
      // quote characters matter as much as the angle brackets.
      expect(neutered('" onmouseover="alert(1)')).toBe(
        '&quot; onmouseover=&quot;alert(1)',
      );
      expect(neutered("' onfocus='alert(1)")).toBe('&#39; onfocus=&#39;alert(1)');
    });

    it('neuters a javascript: URL in an anchor', () => {
      expect(neutered('<a href="javascript:alert(1)">x</a>')).toBe(
        '&lt;a href=&quot;javascript:alert(1)&quot;&gt;x&lt;/a&gt;',
      );
    });

    it('renders the escaped payload as inert text in a real DOM', () => {
      // The strongest assertion available without a browser: hand the escaped
      // string to innerHTML and confirm the DOM sees text, not elements.
      const host = document.createElement('div');
      host.innerHTML = escapeHTML('<script>alert(1)</script><img src=x onerror=y>');
      expect(host.querySelector('script')).toBeNull();
      expect(host.querySelector('img')).toBeNull();
      expect(host.textContent).toBe('<script>alert(1)</script><img src=x onerror=y>');
    });
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
