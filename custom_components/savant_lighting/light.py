from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Light from a config entry."""
    config = entry.data
    name = config["name"]
    host = config["host"]
    port = config["port"]

    async_add_entities([SavantLight(name, host, port)])

class SavantLight(LightEntity):
    """Representation of a Savant Light."""

    def __init__(self, name, host, port):
        """Initialize the light."""
        self._name = name
        self._host = host
        self._port = port
        self._state = False
        self._brightness = 255
        self._hs_color = (0, 0)
        self._supported_color_modes = {ColorMode.HS}
        self._color_mode = ColorMode.HS

    @property
    def supported_color_modes(self):
        """Return the supported color modes."""
        return self._supported_color_modes

    @property
    def color_mode(self):
        """Return the current color mode."""
        return self._color_mode

    @property
    def unique_id(self):
        """Return a unique ID for this light."""
        return f"{self._host}_{self._port}_{self._name}_light"

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def hs_color(self):
        """Return the color of the light."""
        return self._hs_color

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        self._state = True
        if "brightness" in kwargs:
            self._brightness = kwargs["brightness"]
        if "hs_color" in kwargs:
            self._hs_color = kwargs["hs_color"]
            self._color_mode = ColorMode.HS

        await self._send_state_to_device()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        self._state = False

        await self._send_state_to_device()
        self.async_write_ha_state()

    async def _send_state_to_device(self):
        """Send the state to the device."""
        pass

    async def async_update(self):
        """Fetch new state data for this light."""
        if not self.entity_id:
            return

        self._state = True
        self._brightness = 255
        self._hs_color = (0, 0)
        self._color_mode = ColorMode.HS

        self.async_write_ha_state()
