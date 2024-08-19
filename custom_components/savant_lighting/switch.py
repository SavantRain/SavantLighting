import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Lighting switches from a config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    name = config["name"]
    host = config["host"]
    port = config["port"]
    identifier = config.get("identifier", None)
    device_id = config["device_id"]

    # 创建一个自定义的开关实体并添加到 Home Assistant
    async_add_entities([SavantSwitch(name, host, port, identifier, device_id)], update_before_add=True)

class SavantSwitch(SwitchEntity):
    """Representation of a Savant Switch."""

    def __init__(self, name, host, port, identifier, device_id):
        """Initialize the switch."""
        self._name = name
        self._host = host
        self._port = port
        self._identifier = identifier
        self._state = False
        self._device_id = device_id


    @property
    def name(self):
        """Return the display name of this light."""
        return self._name
    
    @property
    def unique_id(self):
        """Return a unique ID for this light."""
        # This is no longer needed as unique_id is defined in entity_registry
        return f"{self._host}_{self._port}_{self._name}_switch"

    @property
    def device_id(self):
        return self._device_id
    
    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._host}:{self._port}_{self._name}")}
        }
        
    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        self._state = True
        await self._send_state_to_device()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        self._state = False
        await self._send_state_to_device()
        self.async_write_ha_state()

    async def _send_state_to_device(self):
        """Send the state to the device."""
        # 这里添加与实际设备的通信逻辑，例如通过网络协议
        _LOGGER.debug(f"Switch {self._name} state set to {self._state}")
