"""Config flow for the Example Integration.

A single-instance integration with no configuration: the user just adds it. The
flow exists so the integration is installable from the UI (and so the template
demonstrates the config-flow + ``strings.json`` localization pattern). Extend
this with a data schema for your own integration's options.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN, PANEL_TITLE


class ExampleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Example Integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step — single instance, no input required."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is None:
            return self.async_show_form(step_id="user")
        return self.async_create_entry(title=PANEL_TITLE, data={})
