"""Drift guard for the integrator-facing API surface (no HA runtime).

``api_surface.py`` claims to be the single index of every surface an integrator can
build on. These checks make that claim enforceable: a service registered without a
``ServiceSpec``, an event named in ``const.py`` and never modelled, a websocket
command whose decorator and registration disagree, a payload field added to
``events.py`` and described nowhere — each fails here rather than shipping.

The technique is the one ``test_exception_translations.py`` already uses: parse the
component's own source with :mod:`ast` and compare it to the model. Static analysis
is brittle when it has to *infer*; here it only reads string literals (and one
``f"{DOMAIN}/…"`` shape) out of a handful of registration calls, and every one of
them has that form today.

**Where these checks can be fooled.** They read literals, so they see what the source
says and not what it computes. A service registered with a name built at runtime, a
websocket ``type`` that is neither a constant nor the ``f"{DOMAIN}/…"`` shape
:func:`_ws_type` understands, or a static path registered somewhere other than
``panel.py`` would each pass unnoticed. Every one of those is a departure from how
the component is written today, which is why literal-reading is enough. If you
introduce one, widen this file rather than trusting it.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import ex.api_surface as api_surface
import ex.const as const
import ex.events as events
import pytest

_COMPONENT = (
    Path(__file__).resolve().parents[2] / "custom_components" / "example_integration"
)
_INIT_TREE = ast.parse((_COMPONENT / "__init__.py").read_text(encoding="utf-8"))
_WS_TREE = ast.parse((_COMPONENT / "websocket_api.py").read_text(encoding="utf-8"))
_PANEL_TREE = ast.parse((_COMPONENT / "panel.py").read_text(encoding="utf-8"))
_SURFACE_TREE = ast.parse((_COMPONENT / "api_surface.py").read_text(encoding="utf-8"))
_STRINGS = json.loads((_COMPONENT / "strings.json").read_text(encoding="utf-8"))


def _services_yaml() -> dict:
    """``services.yaml``, parsed.

    PyYAML is the one dependency beyond ``pytest`` this tier wants, and the README
    promises `pip install pytest` is enough — so the two checks that read
    ``services.yaml`` skip without it and the other two dozen still run. CI installs
    it via ``requirements-test.txt``, so the skip never happens there.
    """
    yaml = pytest.importorskip("yaml", reason="PyYAML not installed")
    return yaml.safe_load((_COMPONENT / "services.yaml").read_text(encoding="utf-8"))


_FIX = "Add or update its spec in custom_components/example_integration/api_surface.py."


# ── Source introspection helpers ─────────────────────────────────────────────


def _kwarg(call: ast.Call, name: str) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _ws_type(node: ast.expr) -> str | None:
    """Resolve a websocket ``type`` value to its runtime string, or None.

    The commands are declared as ``f"{DOMAIN}/list"``, so this understands a plain
    constant *and* an f-string whose only interpolation is the ``DOMAIN`` name. Any
    other shape returns None and is reported as unreadable rather than skipped, so a
    command that stops being introspectable cannot quietly drop out of the checks.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if not isinstance(node, ast.JoinedStr):
        return None
    out = ""
    for part in node.values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            out += part.value
        elif (
            isinstance(part, ast.FormattedValue)
            and isinstance(part.value, ast.Name)
            and part.value.id == "DOMAIN"
        ):
            out += const.DOMAIN
        else:
            return None
    return out


def _service_registrations() -> list[tuple[str, str]]:
    """``(service name, response kind)`` per ``hass.services.async_register`` call."""
    found: list[tuple[str, str]] = []
    for node in ast.walk(_INIT_TREE):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "async_register"):
            continue
        owner = func.value
        if not (isinstance(owner, ast.Attribute) and owner.attr == "services"):
            continue
        assert len(node.args) >= 3 and isinstance(node.args[1], ast.Constant), (
            "a service is registered with a non-literal name, which this drift "
            "guard cannot read. See the module docstring."
        )
        response = "none"
        if (supports := _kwarg(node, "supports_response")) is not None:
            # ``SupportsResponse.OPTIONAL`` -> "optional"
            response = ast.unparse(supports).rsplit(".", 1)[-1].lower()
        found.append((node.args[1].value, response))
    return found


def _websocket_decorations() -> dict[str, str]:
    """``{command type: handler function name}`` from the decorators."""
    found: dict[str, str] = {}
    for node in ast.walk(_WS_TREE):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not (
                isinstance(func, ast.Attribute) and func.attr == "websocket_command"
            ):
                continue
            schema = decorator.args[0]
            assert isinstance(schema, ast.Dict), (
                f"{node.name}'s websocket_command schema is not a dict literal."
            )
            for key, value in zip(schema.keys, schema.values, strict=True):
                if "type" not in ast.unparse(key):
                    continue
                resolved = _ws_type(value)
                assert resolved is not None, (
                    f"{node.name}'s websocket `type` is not a readable literal. "
                    "See the module docstring."
                )
                found[resolved] = node.name
    return found


def _registered_websocket_handlers() -> set[str]:
    """Handler names passed to ``async_register_command`` in ``async_register``."""
    found: set[str] = set()
    for node in ast.walk(_WS_TREE):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute) and func.attr == "async_register_command"
        ):
            continue
        found.add(ast.unparse(node.args[-1]))
    return found


def _static_path_registrations() -> set[str]:
    """The ``StaticPathConfig(url, …)`` urls registered in ``panel.py``."""
    found: set[str] = set()
    for node in ast.walk(_PANEL_TREE):
        if not isinstance(node, ast.Call):
            continue
        if ast.unparse(node.func).rsplit(".", 1)[-1] != "StaticPathConfig":
            continue
        found.add(ast.unparse(node.args[0]))
    return found


# ── Services ─────────────────────────────────────────────────────────────────


def test_every_registered_service_is_modelled() -> None:
    registered = {name for name, _ in _service_registrations()}
    modelled = set(api_surface.SERVICE_NAMES)
    assert registered, "no service registrations found — the AST reader is broken"
    assert registered == modelled, (
        f"services registered but not modelled: {sorted(registered - modelled)}; "
        f"modelled but not registered: {sorted(modelled - registered)}. {_FIX}"
    )


def test_service_names_are_unique() -> None:
    assert len(api_surface.SERVICE_NAMES) == len(set(api_surface.SERVICE_NAMES))


def test_service_teardown_iterates_the_model() -> None:
    """``async_unload_entry`` must remove services from ``SERVICE_NAMES``.

    A local tuple repeated in the teardown is how a service ends up registered and
    never removed: it is added in one place and the other is forgotten, and nothing
    fails until a reload leaves a stale service behind.
    """
    unload = next(
        node
        for node in ast.walk(_INIT_TREE)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_unload_entry"
    )
    removals = [
        node
        for node in ast.walk(unload)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "async_remove"
    ]
    assert removals, "async_unload_entry removes no services"
    loops = [node for node in ast.walk(unload) if isinstance(node, ast.For)]
    assert any(ast.unparse(loop.iter) == "SERVICE_NAMES" for loop in loops), (
        "async_unload_entry must iterate api_surface.SERVICE_NAMES, not a local list."
    )


def test_service_response_kind_matches_source() -> None:
    from_source = dict(_service_registrations())
    for spec in api_surface.SERVICES:
        assert from_source[spec.name] == spec.response, (
            f"{spec.name} registers supports_response={from_source[spec.name]!r} "
            f"but the model says {spec.response!r}. {_FIX}"
        )


def test_service_response_kinds_are_known() -> None:
    for spec in api_surface.SERVICES:
        assert spec.response in ("none", "optional", "only"), spec.name


def test_services_yaml_matches_model() -> None:
    declared = set(_services_yaml())
    assert declared == set(api_surface.SERVICE_NAMES), (
        "services.yaml and api_surface.SERVICES disagree: "
        f"{sorted(declared ^ set(api_surface.SERVICE_NAMES))}. {_FIX}"
    )


def test_service_strings_match_model() -> None:
    assert set(_STRINGS["services"]) == set(api_surface.SERVICE_NAMES), (
        "strings.json's `services` section and api_surface.SERVICES disagree: "
        f"{sorted(set(_STRINGS['services']) ^ set(api_surface.SERVICE_NAMES))}. {_FIX}"
    )


@pytest.mark.parametrize("service", api_surface.SERVICE_NAMES)
def test_service_fields_match_between_yaml_and_strings(service: str) -> None:
    """Every ``services.yaml`` field needs a label, and vice versa.

    hassfest checks this too, but only for the shape it knows; doing it here keeps
    the failure in the fast tier where a contributor sees it first.
    """
    yaml_fields = set(_services_yaml()[service].get("fields", {}))
    string_fields = set(_STRINGS["services"][service].get("fields", {}))
    assert yaml_fields == string_fields, (
        f"{service}: services.yaml has {sorted(yaml_fields)}, strings.json has "
        f"{sorted(string_fields)}."
    )


# ── Events ───────────────────────────────────────────────────────────────────


def _const_event_names() -> dict[str, str]:
    """``{const attribute: value}`` for every ``EVENT_*`` in ``const.py``."""
    return {
        name: getattr(const, name)
        for name in dir(const)
        if name.startswith("EVENT_") and isinstance(getattr(const, name), str)
    }


def test_every_const_event_is_modelled() -> None:
    declared = _const_event_names()
    modelled = {spec.const_name: spec.name for spec in api_surface.EVENTS}
    assert declared, "no EVENT_* constants found — the reader is broken"
    unmodelled = sorted(set(declared) - set(modelled))
    invented = sorted(set(modelled) - set(declared))
    assert set(declared) == set(modelled), (
        f"events in const.py but not modelled: {unmodelled}; "
        f"modelled but absent from const.py: {invented}. {_FIX}"
    )


def test_event_specs_reference_the_constant_not_a_retyped_literal() -> None:
    declared = _const_event_names()
    for spec in api_surface.EVENTS:
        assert spec.name == declared[spec.const_name], (
            f"{spec.const_name} is {declared[spec.const_name]!r} in const.py but "
            f"{spec.name!r} in the model. Reference the constant, never re-type it."
        )


def test_every_fired_event_has_a_summary() -> None:
    missing = [
        spec.name
        for spec in api_surface.EVENTS
        if spec.direction == "fired" and not spec.summary
    ]
    assert not missing, (
        f"fired events with no 'fires when' summary: {missing}. A bus event has no "
        "Home Assistant string source, so the summary lives in the model."
    )


def test_event_directions_and_payloads_are_known() -> None:
    for spec in api_surface.EVENTS:
        assert spec.direction in ("fired", "listened"), spec.name
        assert spec.payload == "none" or spec.payload in api_surface.PAYLOAD_SPINES, (
            f"{spec.name} names payload spine {spec.payload!r}, which is not in "
            f"PAYLOAD_SPINES. {_FIX}"
        )


def test_payload_spines_match_the_event_builders() -> None:
    """The documented payload and the shipped one must be the same keys.

    Calling the real builders is the point: a key added to ``events.py`` and not to
    the model fails here, which is the drift that otherwise reaches an integrator as
    an undocumented field.
    """
    item = {"id": "abc", "name": "Shelf", "value": 3}
    spine = {field.name for field in api_surface.PAYLOAD_SPINES["item"]}

    assert set(events.item_event_data(item)) == spine, (
        f"events.item_event_data returns {sorted(events.item_event_data(item))}, "
        f"the model documents {sorted(spine)}. {_FIX}"
    )

    built = {
        const.EVENT_ITEM_CREATED: events.item_created_event_data(item),
        const.EVENT_ITEM_UPDATED: events.item_updated_event_data(item, ["value"]),
        const.EVENT_ITEM_DELETED: events.item_deleted_event_data(item),
    }
    for spec in api_surface.events_by_payload("item"):
        expected = spine | {field.name for field in spec.extra}
        assert set(built[spec.name]) == expected, (
            f"{spec.name} ships {sorted(built[spec.name])}, the model documents "
            f"{sorted(expected)}. {_FIX}"
        )


def test_every_fired_event_payload_is_covered_by_a_builder_check() -> None:
    """Guards the check above from going vacuous when a spine is added.

    ``test_payload_spines_match_the_event_builders`` only exercises the ``item``
    spine. A second spine added to the model with no builder comparison would leave
    that check passing while documenting nothing, so fail here until this file grows
    the comparison too.
    """
    covered = {"item"}
    payloads = {
        spec.payload
        for spec in api_surface.EVENTS
        if spec.direction == "fired" and spec.payload != "none"
    }
    assert payloads <= covered, (
        f"payload spine(s) {sorted(payloads - covered)} are modelled but no test "
        "compares them against the builders in events.py. Extend "
        "test_payload_spines_match_the_event_builders."
    )


# ── Device triggers and options (empty in the template) ──────────────────────


def test_device_triggers_and_options_stay_declared_absent() -> None:
    """Both tables are empty, and SURFACE_KINDS has to say so out loud.

    An empty table is only honest while something explains the absence. If a fork
    adds a ``device_trigger.py`` or an options flow, this test is the reminder to
    update the ledger row rather than leaving it claiming the surface is unused.
    """
    statuses = {kind.kind: kind.status for kind in api_surface.SURFACE_KINDS}
    if not api_surface.DEVICE_TRIGGERS:
        assert statuses["Device triggers"] == "not_applicable"
    if not api_surface.OPTIONS:
        assert statuses["Config entry options"] == "not_applicable"


# ── Entity platforms ─────────────────────────────────────────────────────────


def test_entity_platforms_match_const_and_strings() -> None:
    modelled = {spec.platform for spec in api_surface.ENTITY_PLATFORMS}
    assert modelled == set(const.PLATFORMS), (
        f"const.PLATFORMS is {sorted(const.PLATFORMS)} but the model has "
        f"{sorted(modelled)}. {_FIX}"
    )
    for spec in api_surface.ENTITY_PLATFORMS:
        declared = set(_STRINGS.get("entity", {}).get(spec.platform, {}))
        assert set(spec.translation_keys) <= declared, (
            f"{spec.platform} claims translation key(s) "
            f"{sorted(set(spec.translation_keys) - declared)} that strings.json's "
            f"entity.{spec.platform} section does not define."
        )


# ── Websocket commands ───────────────────────────────────────────────────────


def test_every_websocket_command_is_modelled() -> None:
    declared = set(_websocket_decorations())
    modelled = {spec.type for spec in api_surface.WEBSOCKET_COMMANDS}
    assert declared, "no websocket commands found — the AST reader is broken"
    assert declared == modelled, (
        f"websocket commands declared but not modelled: {sorted(declared - modelled)}; "
        f"modelled but not declared: {sorted(modelled - declared)}. {_FIX}"
    )


def test_every_websocket_command_is_registered() -> None:
    """A decorated command that ``async_register`` never registers is dead code."""
    decorated = _websocket_decorations()
    registered = _registered_websocket_handlers()
    missing = {
        command: handler
        for command, handler in decorated.items()
        if handler not in registered
    }
    assert not missing, (
        f"websocket command(s) declared but never registered in async_register: "
        f"{missing}."
    )


def test_websocket_commands_name_a_real_service() -> None:
    """A mutating command delegates to a service; the model records which one."""
    for spec in api_surface.WEBSOCKET_COMMANDS:
        if spec.service is not None:
            assert spec.service in api_surface.SERVICE_NAMES, (
                f"{spec.type} claims to delegate to {spec.service!r}, which is not "
                f"a modelled service. {_FIX}"
            )


# ── HTTP routes ──────────────────────────────────────────────────────────────


def test_http_views_match_source() -> None:
    registered = _static_path_registrations()
    assert registered, "no static path registered — the AST reader is broken"
    # panel.py registers `StaticPathConfig(PANEL_STATIC_URL, ...)`, so compare the
    # constant's *name*: the model holds its value, and both resolve to one string.
    assert registered == {"PANEL_STATIC_URL"}, (
        f"panel.py registers static path(s) {sorted(registered)}, which this check "
        "no longer recognises. Update the model and this assertion together."
    )
    assert {view.url for view in api_surface.HTTP_VIEWS} == {const.PANEL_STATIC_URL}, (
        f"HTTP_VIEWS does not match the registered static path. {_FIX}"
    )


# ── The model itself ─────────────────────────────────────────────────────────


def test_api_surface_imports_stay_light() -> None:
    """No Home Assistant imports, and nothing from the integration beyond ``const``.

    The model has to load in the fast unit tier with no HA installed. An import of
    a sibling that pulls in Home Assistant would take that away silently: the tier
    would simply stop being able to load it.
    """
    for node in ast.walk(_SURFACE_TREE):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("homeassistant"), alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not module.startswith("homeassistant"), module
            if node.level:  # relative: `from . import const`
                names = {alias.name for alias in node.names}
                assert names <= {"const"}, (
                    f"api_surface imports {sorted(names - {'const'})} from the "
                    "integration. Keep it to const so it stays loadable without HA."
                )


def test_surface_kind_statuses_are_known() -> None:
    for kind in api_surface.SURFACE_KINDS:
        assert kind.status in api_surface.STATUSES, f"{kind.kind}: {kind.status}"
        assert kind.note, f"{kind.kind} has no note; every row needs a reason."


def test_surface_kinds_are_unique() -> None:
    kinds = [kind.kind for kind in api_surface.SURFACE_KINDS]
    assert len(kinds) == len(set(kinds))


def test_every_populated_table_has_a_surface_kind_row() -> None:
    """Nothing may be modelled without the ledger acknowledging it exists."""
    statuses = {kind.kind: kind.status for kind in api_surface.SURFACE_KINDS}
    populated = {
        "Actions (services)": api_surface.SERVICES,
        "Bus events": api_surface.EVENTS,
        "Device triggers": api_surface.DEVICE_TRIGGERS,
        "Entity platforms": api_surface.ENTITY_PLATFORMS,
        "Config entry options": api_surface.OPTIONS,
        "Websocket commands": api_surface.WEBSOCKET_COMMANDS,
        "HTTP routes": api_surface.HTTP_VIEWS,
    }
    for kind, table in populated.items():
        assert kind in statuses, f"{kind} has no SURFACE_KINDS row. {_FIX}"
        if table:
            assert statuses[kind] != "not_applicable", (
                f"{kind} is marked not_applicable but its table has "
                f"{len(table)} entries."
            )
