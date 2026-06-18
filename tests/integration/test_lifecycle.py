"""Docker integration: the integration loads and its surfaces are live in real HA."""

from __future__ import annotations


def test_config_entry_loaded(api):
    """The example_integration config entry is set up (states API responds)."""
    resp = api.get("/api/states")
    assert resp.status_code == 200


def test_services_registered(api):
    """The automation-facing services exist on the running instance."""
    resp = api.get("/api/services")
    assert resp.status_code == 200
    domains = {block["domain"]: block for block in resp.json()}
    assert "example_integration" in domains
    services = domains["example_integration"]["services"]
    for name in ("add_item", "update_item", "delete_item"):
        assert name in services


def test_panel_bundle_served(api):
    """The sidebar panel JS bundle is served from the static path."""
    resp = api.get("/example_integration_static/example-panel.js")
    assert resp.status_code == 200
    assert "ExamplePanelBundle" in resp.text or "example-panel" in resp.text


def test_card_bundle_served(api):
    """The dashboard card JS bundle is served from the static path."""
    resp = api.get("/example_integration_static/example-card.js")
    assert resp.status_code == 200
