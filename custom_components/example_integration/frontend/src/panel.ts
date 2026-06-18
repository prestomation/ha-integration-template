import { ExampleApi } from './api';
import { setLanguage, t, tn } from './i18n';
import type { HomeAssistant, Item, Route } from './types';
import { buildPath, escapeHTML, formatDate, parseRoute, PanelRoute } from './utils';
import { PANEL_VERSION } from 'panel-version';

/**
 * The Example Integration sidebar panel (a `panel_custom` web component).
 *
 * Navigation is high-fidelity deep-linked: the URL is the single source of
 * truth. HA hands us a `route` for every in-panel URL change (including
 * Back/Forward); the `route` setter is the ONLY place that flips `_nav`. We
 * navigate by changing the URL via `_navigate`, never by mutating `_nav`
 * directly. Route parse/build are pure functions in utils.ts.
 */
export class ExamplePanel extends HTMLElement {
  private _hass?: HomeAssistant;
  private _api?: ExampleApi;
  private _route?: Route;
  private _nav: PanelRoute = { view: 'list', detailId: null };
  private _items: Item[] = [];
  private _loaded = false;
  private _adding = false;
  private _error = '';

  // ── HA-provided properties ────────────────────────────────────────────────
  set hass(hass: HomeAssistant) {
    const first = !this._hass;
    this._hass = hass;
    this._api = new ExampleApi(hass);
    setLanguage(hass.language);
    if (first) {
      void this._refresh();
    }
  }

  set route(route: Route) {
    this._route = route;
    this._nav = parseRoute(route);
    this._render();
  }
  get route(): Route | undefined {
    return this._route;
  }

  set narrow(_v: boolean) {
    /* accepted from HA; layout is responsive via CSS */
  }
  set panel(_v: unknown) {
    /* panel config from HA; unused */
  }

  // ── Navigation ────────────────────────────────────────────────────────────
  /** Change the panel URL; HA re-sets `route`, which flows back through `set route`. */
  private _navigate(state: PanelRoute, replace = false): void {
    const prefix = this._route?.prefix ?? '/example-integration';
    const url = prefix + buildPath(state);
    history[replace ? 'replaceState' : 'pushState'](null, '', url);
    this.dispatchEvent(
      new CustomEvent('location-changed', { bubbles: true, composed: true }),
    );
  }

  // ── Data ──────────────────────────────────────────────────────────────────
  private async _refresh(): Promise<void> {
    if (!this._api) return;
    try {
      this._items = await this._api.list();
      this._error = '';
    } catch (err) {
      this._error = String(err);
    }
    this._loaded = true;
    this._render();
  }

  // ── Render ────────────────────────────────────────────────────────────────
  private _render(): void {
    if (!this._loaded) {
      this.innerHTML = `<div class="ex-loading">…</div>`;
      return;
    }
    const detail = this._nav.detailId
      ? this._items.find((i) => i.id === this._nav.detailId)
      : null;
    if (this._nav.detailId && !detail) {
      this._renderGone();
      return;
    }
    if (detail) {
      this._renderDetail(detail);
      return;
    }
    this._renderList();
  }

  private _styles(): string {
    return `<style>
      .ex-root { padding: 16px; max-width: 720px; margin: 0 auto; font-family: var(--paper-font-body1_-_font-family, sans-serif); }
      .ex-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
      .ex-toolbar-title { font-size: 1.4rem; font-weight: 500; }
      .ex-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border: 1px solid var(--divider-color, #e0e0e0); border-radius: 12px; margin-bottom: 8px; cursor: pointer; background: var(--card-background-color, #fff); }
      .ex-name { font-weight: 500; }
      .ex-value { color: var(--secondary-text-color, #666); }
      .ex-empty, .ex-gone { color: var(--secondary-text-color, #666); padding: 24px 0; }
      .ex-btn { cursor: pointer; border: none; border-radius: 10px; padding: 8px 14px; background: var(--primary-color, #03a9f4); color: #fff; font-size: 0.95rem; }
      .ex-btn.secondary { background: transparent; color: var(--primary-color, #03a9f4); }
      .ex-form { border: 1px solid var(--divider-color, #e0e0e0); border-radius: 12px; padding: 16px; margin-bottom: 16px; background: var(--card-background-color, #fff); }
      .ex-form label { display: block; font-size: 0.85rem; color: var(--secondary-text-color, #666); margin: 8px 0 4px; }
      .ex-form input { width: 100%; box-sizing: border-box; padding: 8px; border: 1px solid var(--divider-color, #ccc); border-radius: 8px; font-size: 1rem; }
      .ex-form-actions { display: flex; gap: 8px; margin-top: 16px; }
      .ex-error { color: var(--error-color, #db4437); margin: 8px 0; }
      .ex-meta { color: var(--secondary-text-color, #666); font-size: 0.85rem; }
      .ex-foot { color: var(--secondary-text-color, #999); font-size: 0.75rem; margin-top: 24px; text-align: center; }
    </style>`;
  }

  private _renderList(): void {
    const rows = this._items
      .map(
        (i) => `
        <div class="ex-row detail-open" data-detail-id="${escapeHTML(i.id)}">
          <span class="ex-name">${escapeHTML(i.name)}</span>
          <span class="ex-value">${escapeHTML(i.value)}</span>
        </div>`,
      )
      .join('');
    const count = this._items.length
      ? `<div class="ex-meta">${escapeHTML(tn('count', this._items.length))}</div>`
      : '';
    this.innerHTML = `${this._styles()}
      <div class="ex-root">
        <div class="ex-toolbar">
          <span class="ex-toolbar-title">${escapeHTML(t('panel.title'))}</span>
          <button id="add-btn" class="ex-btn">${escapeHTML(t('panel.add'))}</button>
        </div>
        ${this._error ? `<div class="ex-error">${escapeHTML(this._error)}</div>` : ''}
        ${this._adding ? this._formHtml() : ''}
        ${count}
        ${this._items.length ? rows : `<div class="ex-empty">${escapeHTML(t('panel.empty'))}</div>`}
        <div class="ex-foot">v${escapeHTML(PANEL_VERSION)}</div>
      </div>`;
    this._wireList();
  }

  private _formHtml(): string {
    return `
      <form id="ex-item-form" class="ex-form">
        <label for="ex-name">${escapeHTML(t('panel.name'))}</label>
        <input id="ex-name" name="name" type="text" autocomplete="off" />
        <label for="ex-value">${escapeHTML(t('panel.value'))}</label>
        <input id="ex-value" name="value" type="number" value="0" />
        <div class="ex-form-actions">
          <button type="submit" class="ex-btn" id="ex-save">${escapeHTML(t('panel.save'))}</button>
          <button type="button" class="ex-btn secondary" id="ex-cancel">${escapeHTML(t('panel.cancel'))}</button>
        </div>
      </form>`;
  }

  private _wireList(): void {
    this.querySelector('#add-btn')?.addEventListener('click', () => {
      this._adding = !this._adding;
      this._render();
    });
    this.querySelectorAll<HTMLElement>('.detail-open').forEach((el) => {
      el.addEventListener('click', () => {
        const id = el.dataset.detailId!;
        this._navigate({ view: 'list', detailId: id });
      });
    });
    const form = this.querySelector<HTMLFormElement>('#ex-item-form');
    if (form) {
      this.querySelector('#ex-cancel')?.addEventListener('click', () => {
        this._adding = false;
        this._render();
      });
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        void this._submitAdd(form);
      });
    }
  }

  private async _submitAdd(form: HTMLFormElement): Promise<void> {
    const name = (form.elements.namedItem('name') as HTMLInputElement).value.trim();
    const value = Number((form.elements.namedItem('value') as HTMLInputElement).value || '0');
    if (!name) {
      this._error = t('panel.name_required');
      this._render();
      return;
    }
    try {
      await this._api!.add(name, Math.trunc(value));
      this._adding = false;
      await this._refresh();
    } catch (err) {
      this._error = String(err);
      this._render();
    }
  }

  private _renderDetail(item: Item): void {
    this.innerHTML = `${this._styles()}
      <div class="ex-root">
        <div class="ex-toolbar">
          <button id="back-btn" class="ex-btn secondary">← ${escapeHTML(t('panel.back'))}</button>
          <button id="del-btn" class="ex-btn">${escapeHTML(t('panel.delete'))}</button>
        </div>
        <h2 class="ex-name">${escapeHTML(item.name)}</h2>
        <form id="ex-edit-form" class="ex-form">
          <label for="ex-name">${escapeHTML(t('panel.name'))}</label>
          <input id="ex-name" name="name" type="text" value="${escapeHTML(item.name)}" />
          <label for="ex-value">${escapeHTML(t('panel.value'))}</label>
          <input id="ex-value" name="value" type="number" value="${escapeHTML(item.value)}" />
          <div class="ex-form-actions">
            <button type="submit" class="ex-btn">${escapeHTML(t('panel.save'))}</button>
          </div>
        </form>
        <div class="ex-meta">${escapeHTML(t('panel.created'))}: ${escapeHTML(formatDate(item.created))}</div>
        ${this._error ? `<div class="ex-error">${escapeHTML(this._error)}</div>` : ''}
      </div>`;
    this.querySelector('#back-btn')?.addEventListener('click', () =>
      this._navigate({ view: 'list', detailId: null }, true),
    );
    this.querySelector('#del-btn')?.addEventListener('click', () =>
      void this._delete(item.id),
    );
    const form = this.querySelector<HTMLFormElement>('#ex-edit-form');
    form?.addEventListener('submit', (e) => {
      e.preventDefault();
      void this._submitEdit(item.id, form);
    });
  }

  private async _submitEdit(id: string, form: HTMLFormElement): Promise<void> {
    const name = (form.elements.namedItem('name') as HTMLInputElement).value.trim();
    const value = Number((form.elements.namedItem('value') as HTMLInputElement).value || '0');
    if (!name) {
      this._error = t('panel.name_required');
      this._render();
      return;
    }
    try {
      await this._api!.update(id, { name, value: Math.trunc(value) });
      await this._refresh();
    } catch (err) {
      this._error = String(err);
      this._render();
    }
  }

  private async _delete(id: string): Promise<void> {
    try {
      await this._api!.remove(id);
      await this._refresh();
      // Closing a deleted detail is a lateral move -> replace so Back doesn't
      // return to the gone object.
      this._navigate({ view: 'list', detailId: null }, true);
    } catch (err) {
      this._error = String(err);
      this._render();
    }
  }

  private _renderGone(): void {
    this.innerHTML = `${this._styles()}
      <div class="ex-root">
        <div class="ex-toolbar">
          <button id="back-btn" class="ex-btn secondary">← ${escapeHTML(t('panel.back'))}</button>
        </div>
        <div class="ex-gone">${escapeHTML(t('panel.gone'))}</div>
      </div>`;
    this.querySelector('#back-btn')?.addEventListener('click', () =>
      this._navigate({ view: 'list', detailId: null }, true),
    );
  }
}
