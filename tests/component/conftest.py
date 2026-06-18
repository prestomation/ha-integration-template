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

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


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
