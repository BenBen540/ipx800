"""Config flow to configure the ipx800v4 integration."""

from datetime import timedelta
import voluptuous as vol

from homeassistant.config_entries import (
    CONN_CLASS_LOCAL_POLL,
    HANDLERS,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_SCAN_INTERVAL, CONF_PORT
from homeassistant.core import callback

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

# Schema definitions
IPX800_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, description="Name of the IPX800"): str,
        vol.Required(CONF_HOST, description="Hostname or IP address of the IPX800"): str,
        vol.Optional(CONF_PORT, default=80, description="HTTP port"): int,
        vol.Required("api_key", description="API key (activate in Network => API)"): str,
        vol.Optional("username", description="Username (for X-PWM control only)"): str,
        vol.Optional("password", description="Password (for X-PWM control only)"): str,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL, description="Polling interval in seconds"
        ): int,
        vol.Optional("push_password", description="Password for PUSH API calls from IPX800"): str,
    }
)

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required("component", description="Device type"): vol.In(
            ["switch", "light", "cover", "sensor", "binary_sensor"]
        ),
        vol.Required(CONF_NAME, description="Friendly name of the device"): str,
        vol.Optional("device_class", description="Device class for binary sensors/sensors"): str,
        vol.Optional("unit_of_measurement", description="Unit of measurement for sensors"): str,
        vol.Optional("transition", default=500, description="Transition time for lights (ms)"): int,
        vol.Optional("icon", description="Custom icon for the device"): str,
        vol.Required("type", description="Type of input/output on the IPX800"): vol.In(
            [
                "relay",
                "analogin",
                "virtualanalogin",
                "digitalin",
                "virtualin",
                "virtualout",
                "xdimmer",
                "xpwm",
                "xpwm_rgb",
                "xpwm_rgbw",
                "xthl",
                "x4vr",
                "x4fp",
                "relay_fp",
                "counter",
            ]
        ),
        vol.Optional("id", description="ID of type output"): int,
        vol.Optional("ext_id", description="ID of X-4VR extension"): int,
        vol.Optional("ids", default=[], description="IDs of channels for xpwm_rgb, xpwm_rgbw"): list,
        vol.Optional(
            "default_brightness",
            description="Default brightness for lights (1-255)",
            default=255,
        ): vol.All(int, vol.Range(min=1, max=255)),
        vol.Optional("invert_value", default=False, description="Invert value for binary sensors"): bool,
    }
)

@HANDLERS.register(DOMAIN)
class IpxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle an IPX800 config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}
        self.devices = []
        self.device_to_edit = None

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            self.data = user_input
            self.data["devices"] = self.devices
            return self.async_create_entry(title=user_input[CONF_NAME], data=self.data)

        return self.async_show_form(step_id="user", data_schema=IPX800_SCHEMA)

    async def async_step_device_list(self, user_input=None) -> ConfigFlowResult:
        """Show list of devices."""
        if user_input is not None:
            if user_input["action"] == "add":
                return await self.async_step_add_device()
            elif user_input["action"] == "edit":
                self.device_to_edit = user_input["device_index"]
                return await self.async_step_edit_device()
            elif user_input["action"] == "remove":
                self.devices.pop(user_input["device_index"])
        
        device_names = [device[CONF_NAME] for device in self.devices]
        actions = {
            "add": "Add a new device",
            "edit": "Edit an existing device",
            "remove": "Remove a device",
        }

        return self.async_show_menu(
            step_id="device_list",
            menu_options=actions,
            description_placeholders={"devices": "\n".join(device_names) or "No devices added."},
        )

    async def async_step_add_device(self, user_input=None) -> ConfigFlowResult:
        """Add a new device."""
        if user_input is not None:
            self.devices.append(user_input)
            return await self.async_step_device_list()

        return self.async_show_form(step_id="add_device", data_schema=DEVICE_SCHEMA)

    async def async_step_edit_device(self, user_input=None) -> ConfigFlowResult:
        """Edit an existing device."""
        if user_input is not None:
            self.devices[self.device_to_edit] = user_input
            self.device_to_edit = None
            return await self.async_step_device_list()

        device = self.devices[self.device_to_edit]
        return self.async_show_form(
            step_id="edit_device",
            data_schema=vol.Schema(
                {k: v for k, v in DEVICE_SCHEMA.schema.items() if k in device},
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Define the config flow to handle options."""
        return Ipx800OptionsFlowHandler(config_entry)


class Ipx800OptionsFlowHandler(OptionsFlow):
    """Handle IPX800 options."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """Manage the IPX800 options."""
        if user_input is not None:
            scan_interval = timedelta(seconds=user_input[CONF_SCAN_INTERVAL])
            self.hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"].update_interval = scan_interval
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_SCAN_INTERVAL, default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int}
            ),
        )
