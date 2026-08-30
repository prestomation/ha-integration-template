"""The committed Docker-tier fixtures must match what the suites expect of them.

``tests/integration/ha_config`` is bind-mounted into the Home Assistant container, so
running the integration or e2e tier locally rewrites ``.storage/core.config_entries``
in place — Home Assistant adds its own bookkeeping (timestamps, discovery keys,
sub-entries) and bumps the store's ``minor_version``. AGENTS.md says to restore the
fixture before committing, and that instruction is easy to miss: a ``git add -A``
after a local run quietly bakes in whatever the container just wrote.

That is not cosmetic. The seeded entry is what makes the integration load *at HA
startup*, which is what injects the dashboard card resource into served pages. A
fixture carrying a future HA's runtime shape is a fixture that can stop loading on
the version CI actually runs — and it fails on a pristine checkout while passing
locally against the already-dirty container.

The second guard here is a drift check rather than a hygiene one: the e2e dashboard
hardcodes a ``custom:`` card type that nothing in the build resolves against, so
renaming the card element silently leaves the dashboard rendering an error card. The
browser suite would notice; the far cheaper unit tier notices first.

Pure JSON/YAML/text reading, so it runs in the fast unit lane with no Home Assistant.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

HA_CONFIG = ROOT / "tests" / "integration" / "ha_config"
CONFIG_ENTRIES = HA_CONFIG / ".storage" / "core.config_entries"
DASHBOARD = HA_CONFIG / "example-e2e.yaml"
CARD_INDEX = (
    ROOT
    / "custom_components"
    / "example_integration"
    / "frontend"
    / "src"
    / "card-index.ts"
)

RESTORE = (
    "Restore it with `git checkout -- tests/integration/ha_config/` and re-commit."
)

#: Exactly the keys the seed is meant to carry. Anything else is Home Assistant's
#: runtime bookkeeping (``created_at``, ``modified_at``, ``discovery_keys``,
#: ``subentries``, …) written by a local container run. Widening this set is a
#: deliberate edit — do it when a new Home Assistant needs a key to load the entry,
#: never to make a dirty fixture pass.
SEEDED_ENTRY_KEYS = {
    "entry_id",
    "version",
    "minor_version",
    "domain",
    "title",
    "data",
    "options",
    "pref_disable_new_entities",
    "pref_disable_polling",
    "source",
    "unique_id",
    "disabled_by",
}

#: `- type: custom:example-card` in the seeded YAML dashboard.
_YAML_CUSTOM_CARD = re.compile(r"type:\s*custom:([\w-]+)")

#: `customElements.define('example-card', …)` in the card bundle's entry point.
_DEFINED_ELEMENT = re.compile(r"customElements\.define\(\s*['\"]([\w-]+)['\"]")


def _payload() -> dict:
    return json.loads(CONFIG_ENTRIES.read_text(encoding="utf-8"))


def test_seeded_config_entry_carries_no_runtime_state() -> None:
    entries = _payload()["data"]["entries"]
    assert len(entries) == 1, (
        f"the seed should hold exactly one config entry, found {len(entries)}. "
        f"A local container run adds its own. {RESTORE}"
    )

    extra = sorted(set(entries[0]) - SEEDED_ENTRY_KEYS)
    assert not extra, (
        f"the committed config-entry fixture carries key(s) Home Assistant writes at "
        f"runtime: {extra}. That means a local run was committed. {RESTORE}"
    )


def test_seeded_config_entry_still_loads_the_integration() -> None:
    """A hand-restore that drops a required key is as broken as a dirty one.

    Without ``domain`` and ``entry_id`` Home Assistant does not set the integration
    up at startup, and the card resource never reaches served pages — which surfaces
    only as a browser test failing to find the card, several tiers later.
    """
    entry = _payload()["data"]["entries"][0]
    missing = sorted(SEEDED_ENTRY_KEYS - set(entry))
    assert not missing, f"the seeded config entry is missing key(s): {missing}."
    assert entry["domain"] == "example_integration"
    assert entry["entry_id"], "the seeded entry needs a stable entry_id"


def test_storage_envelope_is_the_seed_not_a_migrated_copy() -> None:
    """Home Assistant bumps ``minor_version`` when it rewrites the store."""
    payload = _payload()
    assert payload["key"] == "core.config_entries"
    assert (payload["version"], payload["minor_version"]) == (1, 1), (
        "the config-entry store's version envelope changed, which is what Home "
        f"Assistant does when it rewrites the file. {RESTORE}"
    )


def test_e2e_dashboard_card_type_is_a_registered_element() -> None:
    dashboard_cards = set(_YAML_CUSTOM_CARD.findall(DASHBOARD.read_text()))
    assert dashboard_cards, (
        f"{DASHBOARD.name} declares no `custom:` card — the e2e suite has nothing "
        "to assert the dashboard card against."
    )

    defined = set(_DEFINED_ELEMENT.findall(CARD_INDEX.read_text()))
    unknown = sorted(dashboard_cards - defined)
    assert not unknown, (
        f"the seeded e2e dashboard uses card type(s) {unknown}, which "
        f"{CARD_INDEX.name} never registers — the dashboard would render an error "
        "card. Rename both together."
    )
