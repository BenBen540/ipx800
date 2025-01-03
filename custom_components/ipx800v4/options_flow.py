import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

class MyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the IPX800 integration."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step of configuration."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )
        return self.async_show_form(step_id="user", data_schema=self._get_schema())

    def _get_schema(self):
        """Return the schema for user input."""
        return vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=600)
                ),
                vol.Optional("debug_mode", default=False): bool,
            }
        )

    async def async_step_options(self, user_input=None):
        """Handle updating options."""
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.entry,
                options=user_input,
            )
            # Annuler le flux et signaler que les options ont été mises à jour
            return self.async_abort(reason="options_updated")

        return self.async_show_form(
            step_id="options", data_schema=self._get_schema()
        )
