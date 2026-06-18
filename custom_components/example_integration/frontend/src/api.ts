import type { HomeAssistant, Item } from './types';

// Domain prefix for the websocket commands (mirrors DOMAIN in const.py). The
// commands delegate to the same store methods as the services (see
// websocket_api.py) — this is purely a UI-latency optimization.
const WS = 'example_integration';

/** Thin websocket client the panel and card use to read/mutate items. */
export class ExampleApi {
  constructor(private hass: HomeAssistant) {}

  async list(): Promise<Item[]> {
    const res = await this.hass.callWS<{ items: Item[] }>({ type: `${WS}/list` });
    return res.items;
  }

  async add(name: string, value: number): Promise<Item> {
    const res = await this.hass.callWS<{ item: Item }>({
      type: `${WS}/add`,
      name,
      value,
    });
    return res.item;
  }

  async update(item_id: string, fields: { name?: string; value?: number }): Promise<Item> {
    const res = await this.hass.callWS<{ item: Item }>({
      type: `${WS}/update`,
      item_id,
      ...fields,
    });
    return res.item;
  }

  async remove(item_id: string): Promise<void> {
    await this.hass.callWS({ type: `${WS}/delete`, item_id });
  }
}
