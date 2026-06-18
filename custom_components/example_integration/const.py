"""Constants for the Example Integration.

This is a TEMPLATE integration. The example feature is a managed *items list*:
a set of named items, each carrying a numeric ``value``. It is deliberately
tiny — the point of this repo is the *scaffolding and patterns* around it
(pure core, store chokepoint, events, services, websocket, sidebar panel +
Lovelace card, translations, and the test/CI/agentic-rules harness), not the
feature itself.

To adapt this template, find-and-replace ``example_integration`` /
``Example Integration`` / ``example-`` throughout, then replace the items model
with your own.
"""

DOMAIN = "example_integration"

# Entity platforms forwarded from the config entry. The template ships a single
# ``sensor`` platform (a total + per-item value sensors) to demonstrate the
# coordinator -> entity pattern without a zoo of platforms.
PLATFORMS = ["sensor"]

# Frontend panel + card.
# PANEL_VERSION is the single source of truth that release.yml validates against
# manifest.json's "version". rollup.config.mjs reads it from this file so the
# built bundles are stamped with the same string.
PANEL_VERSION = "0.1.0"
PANEL_URL_PATH = "example-integration"  # sidebar route -> /example-integration
PANEL_STATIC_URL = "/example_integration_static"  # serves the JS bundles
PANEL_JS_FILENAME = "example-panel.js"
PANEL_TITLE = "Example Integration"
PANEL_ICON = "mdi:view-list"
WEBCOMPONENT_NAME = "example-panel"

# Dashboard card. Served from the same static path as the panel and
# auto-registered as a Lovelace resource so it appears in the "Add card" picker
# with no manual setup (see card.py).
CARD_JS_FILENAME = "example-card.js"

# Storage — a single JSON document at ``.storage/example_integration``.
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

# Bounds for item validation (kept in the pure model — no HA imports there).
MAX_NAME_LENGTH = 255
MIN_VALUE = -1_000_000
MAX_VALUE = 1_000_000

# Event catalog (see docs/EVENTS.md). Every observable state change fires a bus
# event built by a pure function in events.py, so automations and other
# integrations can react to the full item lifecycle. Names follow
# ``{DOMAIN}_<noun>_<verb>``; payloads share a common spine
# (events.item_event_data).
EVENT_ITEM_CREATED = f"{DOMAIN}_item_created"
EVENT_ITEM_UPDATED = f"{DOMAIN}_item_updated"  # payload carries ``changed_fields``
EVENT_ITEM_DELETED = f"{DOMAIN}_item_deleted"
