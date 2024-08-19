from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Light from a config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    name = config["name"]
    host = config["host"]
    port = config["port"]
    device_id = config["device_id"]
    
    async_add_entities([SavantLight(name, host, port, device_id)])

class SavantLight(LightEntity):
    """Representation of a Savant Light."""

    def __init__(self, name, host, port, device_id):
        """Initialize the light."""
        self._device_id = device_id
        self._name = name
        self._host = host
        self._port = port
        self._state = False
        self._brightness = 255
        self._hs_color = (0, 0)
        self._supported_color_modes = {ColorMode.HS}
        self._color_mode = ColorMode.HS
        
    @property
    def name(self):
        """Return the display name of this light."""
        return self._name
    
    @property
    def unique_id(self):
        """Return a unique ID for this light."""
        # This is no longer needed as unique_id is defined in entity_registry
        return f"{self._host}_{self._port}_{self._name}_light"

    @property
    def device_id(self):
        return self._device_id
    
    @property
    def supported_color_modes(self):
        """Return the supported color modes."""
        return self._supported_color_modes

    @property
    def color_mode(self):
        """Return the current color mode."""
        return self._color_mode

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

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._host}:{self._port}_{self._name}")}
        }
    
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
