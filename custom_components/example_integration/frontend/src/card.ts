import { ExampleApi } from './api';
import { setLanguage, t } from './i18n';
import type { HomeAssistant, Item } from './types';
import { escapeHTML } from './utils';

export const CARD_NAME = t('card.name');
export const CARD_DESCRIPTION = t('card.description');

interface CardConfig {
  type: string;
  title?: string;
}

/**
 * A dashboard card that lists the items managed by the Example Integration.
 *
 * Usage surface (read-only display) lives in the card; administration (create /
 * edit / delete) lives in the sidebar panel. The card reads via the same
 * websocket API and refreshes when item events fire on the HA bus.
 */
export class ExampleCard extends HTMLElement {
  private _hass?: HomeAssistant;
  private _api?: ExampleApi;
  private _config: CardConfig = { type: '' };
  private _items: Item[] = [];
  private _loaded = false;
  private _unsub?: () => void;

  setConfig(config: CardConfig): void {
    this._config = config;
    this._render();
  }

  getCardSize(): number {
    return Math.max(1, this._items.length);
  }

  static getConfigElement(): HTMLElement {
    return document.createElement('example-card-editor');
  }

  static getStubConfig(): CardConfig {
    return { type: 'custom:example-card' };
  }

  set hass(hass: HomeAssistant) {
    const first = !this._hass;
    this._hass = hass;
    this._api = new ExampleApi(hass);
    setLanguage(hass.language);
    if (first) {
      void this._refresh();
      void this._subscribe();
    }
  }

  disconnectedCallback(): void {
    this._unsub?.();
    this._unsub = undefined;
  }

  private async _subscribe(): Promise<void> {
    if (!this._hass?.connection) return;
    // Re-fetch when any item lifecycle event fires (created/updated/deleted).
    const handler = () => void this._refresh();
    const subs = await Promise.all([
      this._hass.connection.subscribeEvents(handler, 'example_integration_item_created'),
      this._hass.connection.subscribeEvents(handler, 'example_integration_item_updated'),
      this._hass.connection.subscribeEvents(handler, 'example_integration_item_deleted'),
    ]);
    this._unsub = () => subs.forEach((u) => u());
  }

  private async _refresh(): Promise<void> {
    if (!this._api) return;
    try {
      this._items = await this._api.list();
    } catch {
      this._items = [];
    }
    this._loaded = true;
    this._render();
  }

  private _render(): void {
    const title = this._config.title || t('card.title');
    const body = !this._loaded
      ? '…'
      : this._items.length
        ? this._items
            .map(
              (i) =>
                `<div class="ex-card-row"><span>${escapeHTML(i.name)}</span><span class="ex-card-val">${escapeHTML(i.value)}</span></div>`,
            )
            .join('')
        : `<div class="ex-card-empty">${escapeHTML(t('card.empty'))}</div>`;
    this.innerHTML = `
      <ha-card header="${escapeHTML(title)}">
        <div class="ex-card-body">${body}</div>
        <style>
          .ex-card-body { padding: 4px 16px 16px; }
          .ex-card-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--divider-color, #eee); }
          .ex-card-row:last-child { border-bottom: none; }
          .ex-card-val { color: var(--secondary-text-color, #666); }
          .ex-card-empty { color: var(--secondary-text-color, #666); padding: 8px 0; }
        </style>
      </ha-card>`;
  }
}

/** Minimal config editor: just a card title field. */
export class ExampleCardEditor extends HTMLElement {
  private _config: CardConfig = { type: '' };
  private _hass?: HomeAssistant;

  setConfig(config: CardConfig): void {
    this._config = config;
    this._render();
  }

  set hass(hass: HomeAssistant) {
    this._hass = hass;
    setLanguage(hass.language);
  }

  private _render(): void {
    this.innerHTML = `
      <div style="padding: 8px;">
        <label style="display:block; font-size:0.85rem; margin-bottom:4px;">${escapeHTML(t('card.config_title'))}</label>
        <input id="ex-card-title" type="text" style="width:100%; padding:8px;" value="${escapeHTML(this._config.title ?? '')}" />
      </div>`;
    this.querySelector('#ex-card-title')?.addEventListener('input', (e) => {
      const title = (e.target as HTMLInputElement).value;
      this._config = { ...this._config, title };
      this.dispatchEvent(
        new CustomEvent('config-changed', {
          detail: { config: this._config },
          bubbles: true,
          composed: true,
        }),
      );
    });
    void this._hass; // referenced for HA editor contract
  }
}
