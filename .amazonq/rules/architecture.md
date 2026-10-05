---
title: Architecture rules
summary: The admin and usage split, the privilege gate, the pure core, the store chokepoint, entities, options and localized text.
---

# Architecture rules

How the integration is built is in [docs/design/architecture.md](../../docs/design/architecture.md).
This file gives the rules for code that changes it.

## Administration and usage

- **Administration lives in the panel.** Create, edit and delete of items belong there.
  Never put management UI in the card.
- **Usage goes through native entities** (the `sensor` platform) and the card. Prefer
  native entities and Home Assistant's own cards to a custom usage card.
- All writes go through `ExampleStore` (`store.py`). Entities and the panel read through
  `ExampleCoordinator` and never write storage.
- Items are plain JSON-serializable dicts in storage, never model objects.
- A mutation calls `await coordinator.async_refresh()`, not the debounced
  `async_request_refresh()`. The store is local, so an immediate refresh costs little,
  and the debounce cooldown merges quick mutations and makes tests flaky.

## Privilege model

The admin and usage split is also the security boundary ([SECURITY.md](../../docs/SECURITY.md)).

- The example integration registers the panel with `require_admin=False` and has no
  admin-only operation. Every service and websocket command is open to a signed-in user.
  Use the rules below when you add an operation that only an admin can do.
- **Gate both halves of an admin-only operation.** Put `@websocket_api.require_admin` on
  the websocket command. In its service handler, look up `call.context.user_id` and
  raise `Unauthorized` when the user is not an admin. A gate on the command alone is no
  gate: `call_service` goes around it. Set `admin_only=True` on the spec in
  `api_surface.py`, and add the operation to `docs/SECURITY.md`.
- A call with no `context.user_id` comes from an automation or the core and is trusted.
- Raise the bare `Unauthorized`. It is the 1 exception to localized exceptions, and the
  websocket and REST layers map it to `unauthorized` and 401.
- If the panel holds admin-only operations, register it with `require_admin=True`.
- Serve only built assets as a static path. Home Assistant serves static paths before
  authentication.

### How to decide

Use this list for each new service, websocket command, HTTP method and event. Write the
result in the plan's Security section ([pr-workflow.md](pr-workflow.md)).

- **Open: the data a user works with every day,** and a field, file or list that belongs
  to that data. A user who can create a record can also edit and delete it.
- **Open: a read that the card or a native entity needs.**
- **Admin-only: settings and configuration**, and each operation that can send text to a
  place the caller cannot reach.
- **Admin-only: records that own Home Assistant devices**, because Home Assistant
  reserves device registry changes for admins.
- **Admin-only: bulk and whole-store operations**, such as import, export and a
  delete of many records.
- **Admin-only: each operation that shows what Home Assistant hides from a user**, such
  as a template preview or an entity registry list.
- **A reply never leaks.** A reply holds only data that the caller can already read. If
  the reply would leak, project it or gate the operation.
- **An upload always needs a real user.** A signed URL never writes.
- **If no rule fits, ask the maintainer.** Write the answer in the plan, then add the rule
  here.

## Pure core

- `models.py`, `events.py`, `const.py` and `api_surface.py` never import `homeassistant`.
  They unit-test without the HA harness. Mirror this for the core logic of your domain.
- Pass the time in from the caller (`build_item(..., created=dt_util.now().isoformat())`).
  A pure function never reads a clock.
- All datetimes are timezone-aware. Use `homeassistant.util.dt` at the HA boundary.
- The pure model raises `ItemValidationError`. The service handler maps it to a
  localized `ServiceValidationError` at the boundary.

## Entities and devices

How the entities work is in [coordinator-entities](../../docs/design/coordinator-entities.md).

- Entity `unique_id`s are anchored to the item `id`, so they survive a rename.
- Use `has_entity_name` and a `translation_key` for a fixed entity, so its name comes
  from `strings.json`.
- One service device groups the entities of the config entry (`DeviceInfo` with
  `entry_type=SERVICE`).
- **Link an entity to a device that another integration owns through `device_entry`.**
  Never create a second device for that hardware, and never copy its identifiers or
  write its metadata.

## Options

- The example integration has no options flow. When you add one, keep every option key,
  default and coercion in 1 pure module.
- **An options flow merges. It never replaces.** Return a merge of `entry.options` and
  the form input from `async_create_entry`, never `user_input`. Home Assistant stores the
  result as the whole options object, so a raw return deletes every key that the form
  does not show, such as a key that the panel writes.
- Add an `OptionSpec` to `api_surface.OPTIONS` for each key, and change the row in
  `SURFACE_KINDS`.

## Localized text

- **Every user-facing exception is localized.** Construct `ServiceValidationError` and
  `HomeAssistantError` with `translation_domain=DOMAIN`, a `translation_key` in
  `strings.json` `exceptions` and `translation_placeholders`. Never raise with an
  f-string. `tests/unit/test_exception_translations.py` fails on one.
- A websocket command answers with `connection.send_error`. Its message is shown as is,
  so it is not localized ([IDEAS.md](../../IDEAS.md#localized-websocket-errors)).
