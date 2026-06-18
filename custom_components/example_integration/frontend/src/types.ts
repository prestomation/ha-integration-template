// Minimal shared types for the Example Integration frontend.

/** An item as returned by the backend store / websocket API. */
export interface Item {
  id: string;
  name: string;
  value: number;
  created: string;
}

/** The subset of HA's `hass` object the panel and card use. */
export interface HomeAssistant {
  language?: string;
  callWS<T = unknown>(msg: Record<string, unknown>): Promise<T>;
  connection?: {
    subscribeEvents(cb: (ev: unknown) => void, eventType: string): Promise<() => void>;
  };
}

/** HA hands the panel this for every in-panel URL change (incl. Back/Forward). */
export interface Route {
  prefix: string;
  path: string;
}
