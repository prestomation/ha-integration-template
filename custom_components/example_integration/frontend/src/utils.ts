import type { Route } from './types';

/** Escape user-provided text before injecting into innerHTML. */
export function escapeHTML(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Parsed in-panel navigation state. The URL is the single source of truth for
 * the panel; this and `buildPath` are pure so they unit-test and round-trip
 * losslessly. Scheme: `/` (list) and `/items/<id>` (detail).
 */
export interface PanelRoute {
  view: 'list';
  detailId: string | null;
}

/** Parse the panel-relative `route.path` into navigation state. */
export function parseRoute(route: Route | undefined): PanelRoute {
  const path = (route?.path || '').replace(/^\/+|\/+$/g, '');
  const parts = path ? path.split('/') : [];
  if (parts[0] === 'items' && parts[1]) {
    return { view: 'list', detailId: decodeURIComponent(parts[1]) };
  }
  return { view: 'list', detailId: null };
}

/** Build a panel-relative path from navigation state (inverse of parseRoute). */
export function buildPath(state: PanelRoute): string {
  if (state.detailId) return `/items/${encodeURIComponent(state.detailId)}`;
  return '/';
}

/** Format an ISO timestamp as a short local date, or '' if unparseable. */
export function formatDate(iso: string | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  return isNaN(d.getTime()) ? '' : d.toLocaleDateString();
}
