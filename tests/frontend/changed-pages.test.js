import {describe, it, expect} from 'vitest';
import {
  COMMENT_MARKER,
  pagesForChanges,
  renderComment,
} from '../../website/scripts/changed-pages.mjs';
import {DEV_DOCS, DOC_ROUTES} from '../../website/scripts/doc-map.mjs';

describe('pagesForChanges', () => {
  it('maps changed guide files to their User Guide routes in sidebar order', () => {
    const pages = pagesForChanges({
      changedFiles: ['docs/guide/automation/services.md', 'docs/guide/start/panel.md'],
    });
    expect(pages).toEqual([
      {title: 'The panel', route: '/docs/guide/panel'},
      {title: 'Services', route: '/docs/guide/services'},
    ]);
  });

  it('links no page for the README, which is no longer on the site', () => {
    expect(pagesForChanges({changedFiles: ['README.md']})).toEqual([]);
  });

  it('maps developer docs, changelog and hand-authored pages', () => {
    const pages = pagesForChanges({
      changedFiles: [
        'docs/INTEGRATING.md',
        'docs/EVENTS.md',
        'CHANGELOG.md',
        'website/docs/intro.md',
        'website/src/pages/index.tsx',
      ],
    });
    expect(pages).toEqual([
      {title: 'Integrating with Example Integration', route: '/developer/integrating'},
      {title: 'Events reference', route: '/developer/events'},
      {title: 'Release Notes', route: '/docs/release-notes'},
      {title: 'Introduction', route: '/docs/intro'},
      {title: 'Home (landing page)', route: '/'},
    ]);
  });

  it('maps the API reference\u2019s generation sources to its route', () => {
    // The page has no canonical Markdown file, so a PR that only adds a service
    // or an event would otherwise show no changed doc page at all.
    for (const source of [
      'custom_components/example_integration/api_surface.py',
      'custom_components/example_integration/services.yaml',
      'custom_components/example_integration/strings.json',
    ]) {
      expect(pagesForChanges({changedFiles: [source]})).toEqual([
        {title: 'API reference', route: '/developer/api'},
      ]);
    }
  });

  it('ignores files with no page mapping', () => {
    expect(
      pagesForChanges({changedFiles: ['custom_components/example_integration/store.py']}),
    ).toEqual([]);
  });

  it('de-duplicates repeated routes', () => {
    const pages = pagesForChanges({
      changedFiles: ['docs/EVENTS.md', 'docs/EVENTS.md'],
    });
    expect(pages).toEqual([
      {title: 'Events reference', route: '/developer/events'},
    ]);
  });
});

describe('renderComment', () => {
  const base = 'https://prestomation.github.io/ha-integration-template/pr-preview/pr-9/';

  it('renders a marked, bulleted list with absolute preview URLs', () => {
    const body = renderComment(
      [{title: 'Services', route: '/docs/guide/services'}],
      base,
    );
    expect(body).toContain(COMMENT_MARKER);
    expect(body).toContain(
      '- [Services](https://prestomation.github.io/ha-integration-template/pr-preview/pr-9/docs/guide/services)',
    );
  });

  it('collapses a trailing slash so routes are not doubled', () => {
    const body = renderComment([{title: 'Home', route: '/'}], base);
    expect(body).toContain(
      '- [Home](https://prestomation.github.io/ha-integration-template/pr-preview/pr-9/)',
    );
    expect(body).not.toContain('pr-9//');
  });

  it('still emits the marker when nothing changed', () => {
    const body = renderComment([], base);
    expect(body).toContain(COMMENT_MARKER);
    expect(body).toContain('No documentation pages changed');
  });
});

describe('DOC_ROUTES', () => {
  it('has a route for every published Developer Guide doc', () => {
    // A doc in DEV_DOCS is served on this site, so a relative link to it from
    // another canonical doc should resolve here — not rewrite to a GitHub blob
    // URL. A doc with no route sends every link to it off the site.
    const missing = DEV_DOCS.map((d) => d.file).filter((f) => !DOC_ROUTES[f]);
    expect(missing).toEqual([]);
  });

  it('routes match the page each doc is generated into', () => {
    for (const doc of DEV_DOCS) {
      expect(DOC_ROUTES[doc.file]).toBe(
        `/developer/${doc.out.replace(/\.md$/, '')}`,
      );
    }
  });
});
