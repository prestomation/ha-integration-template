---
title: Security model
summary: What admins and non-admin users can do with the integration, and how to gate a new admin operation, for maintainers and admins.
---

# Security model

Only an admin can manage the configuration of the integration. Any signed-in user can
use its data. Administration is in the panel.
Usage is through native entities and the dashboard card.

## The rule

A Home Assistant instance usually has 1 or 2 admins and a few users, such as a partner,
older children, a housemate, or a guest account on a wall tablet.

Home Assistant reserves Settings and Developer tools for admins. It also restricts the
changes that its own `config/*` commands make to admins. These include changes to the
device registry, the entity registry and config entries. An integration that follows
the same rule gives a guest account no way to change the setup of the home.

## The example integration

The example feature has no admin-only operation, because an item holds no setting and no
private data. Any signed-in user can:

- Open the panel in the sidebar. The panel is registered with `require_admin=False`.
- Read, create, edit and delete items through the services, the websocket commands, the
  panel and the card.
- Read the item sensors and their attributes.

Home Assistant serves the static path of the panel and the card before authentication.
The path is the `frontend/` directory. The release zip leaves the TypeScript sources and
the build files out of it, so an install serves only the built bundles.

## Add an admin-only operation

Gate the operation in 2 places: the websocket command that the panel uses, and the
matching `example_integration.*` service.

1. Put `@websocket_api.require_admin` on the websocket command.
2. In the service handler, read `call.context.user_id`. If it is set, look up the user
   with `hass.auth.async_get_user` and raise `Unauthorized` when the user is not an admin.
3. Set `admin_only=True` on the spec in `api_surface.py`.
4. Add the operation to a table of admin-only operations in this file.
5. If the panel then holds admin-only operations, register it with `require_admin=True`.

A websocket command and its service twin share one authenticated connection. If you
gate only the websocket command, `call_service` bypasses the gate.

A call with no user, such as a scheduled automation, comes from the core. The
integration trusts it the same way Home Assistant does.

The rules that decide if a new operation is admin-only or open are in
[the architecture rules](../.amazonq/rules/architecture.md#how-to-decide). Each PR lists
the surfaces that it adds or changes in its **Security** section.

## Files and links

The example integration stores no files. Accept an upload only from a real
authenticated user. Serve a stored file through an authenticated view. A signed URL
is a bearer credential: anyone who has the link can read the file until it expires. Home
Assistant accepts a signature on `GET` and `HEAD` requests only, so a signed URL can
never write.
