---
sidebar_position: 1
slug: /intro
title: Introduction
---

# Example Integration

Example Integration is a template for a Home Assistant custom integration. Its feature
is a list of **items**. Each item has a name and an integer value.

![The panel with a list of items](/img/screenshots/panel-list.png)

## Features

- **Panel.** Create, edit and delete items in a panel in the Home Assistant sidebar.
- **Entities.** Each item has a `sensor` entity. A total sensor holds the number of items.
- **Dashboard card.** A card lists the items and their values.
- **Services.** Each data action is an `example_integration.*` service.
- **Events.** Each change fires a bus event for automations.
- **Translations.** The text follows the Home Assistant language.

## Next steps

- Start with [Installation](/docs/guide/installation), then read about
  [the panel](/docs/guide/panel).
- To use the integration from another integration, read the
  [Developer Guide](/developer/integrating).
