"""Touch every user-facing surface once, so the Home Assistant log can show problems.

The CI log gate (``scripts/check_ha_log.py``) reads the container log after all
tests ran. It can only find a problem in code that ran. These tests call:

- the diagnostics download (REST endpoint)
- the config flow (a second start must abort, not crash)
- each service, 1 time with valid data

They check that each call works. The log gate checks what the calls wrote to the
log. Add a test here when your integration gets a new surface, for example an
options flow, a repair or a device trigger.
"""

from __future__ import annotations

import time

DOMAIN = "example_integration"


def _entry_id(api) -> str:
    entries = api.get("/api/config/config_entries/entry").json()
    ours = [e for e in entries if e["domain"] == DOMAIN]
    assert ours, "no config entry for the integration"
    return ours[0]["entry_id"]


def test_diagnostics_download(api):
    """Download diagnostics the way the Home Assistant UI does."""
    resp = api.get(f"/api/diagnostics/config_entry/{_entry_id(api)}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Home Assistant wraps the integration data under "data".
    assert "data" in body, f"no 'data' key; body keys: {sorted(body)}"
    data = body["data"]
    for key in ("entry", "items"):
        assert key in data, f"missing diagnostics key {key}; data keys: {sorted(data)}"
    assert data["entry"]["domain"] == DOMAIN


def test_second_config_flow_aborts(api):
    """The integration is single-instance: a second flow ends with an abort."""
    resp = api.post("/api/config/config_entries/flow", json={"handler": DOMAIN})
    assert resp.status_code == 200, resp.text
    assert resp.json()["type"] == "abort", resp.json()


def test_every_service_once(api):
    """Call each service one time with valid data."""
    name = f"surface-{int(time.time())}"
    base = f"/api/services/{DOMAIN}"

    created = api.post(
        f"{base}/add_item?return_response", json={"name": name, "value": 1}
    )
    assert created.status_code == 200, created.text
    item_id = created.json()["service_response"]["item_id"]
    try:
        updated = api.post(
            f"{base}/update_item", json={"item_id": item_id, "name": name, "value": 2}
        )
        assert updated.status_code == 200, updated.text
    finally:
        deleted = api.post(f"{base}/delete_item", json={"item_id": item_id})
    assert deleted.status_code == 200, deleted.text
