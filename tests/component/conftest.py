"""Fixtures for the component tier (real in-process Home Assistant).

These tests run against a REAL Home Assistant runtime provided by
``pytest-homeassistant-custom-component`` — real ``hass``, real entity/device
registries, real config entries — with I/O mocked. They are fast (~100ms) and
test the HA-coupled code (setup, store, coordinator, sensor entities, services,
events on the bus, websocket commands) that the pure unit tier cannot.

This tier pulls in ``pytest-socket`` (blocks real network); never run it in the
same invocation as the Docker integration tier.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from blockbuster import BlockBuster, blockbuster_ctx

pytest_plugins = "pytest_homeassistant_custom_component"

# CHANGE THIS when you rename the template: the package whose code the blockbuster
# fixture watches. (scripts/rename.py rewrites it for you.)
SCANNED_MODULE = "custom_components.example_integration"


@pytest.fixture(autouse=True)
def blockbuster() -> Iterator[BlockBuster]:
    """Fail a test when code blocks the event loop thread.

    Blockbuster patches file, socket, sleep and similar calls. When such a call
    runs while an event loop runs in the same thread, it raises BlockingError.
    The message has the exact file and line. Home Assistant gives the same
    warning at run time ("Detected blocking call"); this fixture finds the
    problem in the component tests instead.

    The check covers only calls that have a frame of this integration on the
    stack (``scanned_modules``). Home Assistant core and the test harness make
    some blocking calls of their own, for example in the frontend setup, and
    those are not ours to fix. This also matches the run-time warning, which
    names "custom integration" only for our code.

    The check lives in this tier because the pure unit tier has no event loop
    and no Home Assistant.
    """
    with blockbuster_ctx(scanned_modules=[SCANNED_MODULE]) as bb:
        yield bb


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load ``custom_components/example_integration`` in every component test."""
    yield


@pytest.fixture
async def setup_entry(hass):
    """Set up the integration from a fresh config entry and return it."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.example_integration.const import DOMAIN

    entry = MockConfigEntry(domain=DOMAIN, title="Example Integration", data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
