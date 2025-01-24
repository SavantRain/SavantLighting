import logging
from datetime import timedelta
from homeassistant.components.switch import SwitchEntity
from .command_helper import SwitchCommand
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

class SavantSwitch8Button(SwitchEntity):
    """Representation of an 8-button switch."""

    def __init__(self, name, module_address, loop_address, button_index, host, port, tcp_manager):
        """Initialize the 8-button switch."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._button_index = button_index  # 当前按键的索引 (1-8)
        self._host = host
        self._port = port
        self._is_on = False
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("8button", self.update_state)
        self.command = SwitchCommand(host, module_address, loop_address)

    @property
    def unique_id(self):
        """Return a unique ID for this switch button."""
        return f"{self._module_address}_{self._loop_address}_{self._button_index}_8button"

    @property
    def is_on(self):
        """Return true if the button is on."""
        return self._is_on

    @property
    def name(self):
        """Return the name of the button."""
        return f"{self._attr_name} Button {self._button_index}"
    
    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Switch 8 Buttons Model",
        }
        
    async def async_turn_on(self, **kwargs):
        """Turn the button on."""
        self._is_on = True
        await self._send_state_to_device(f"button:{self._button_index}:on")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the button off."""
        self._is_on = False
        await self._send_state_to_device(f"button:{self._button_index}:off")
        self.async_write_ha_state()
        
    def update_state(self, response_dict):
        """Update the state of the button based on the response."""
        button_index = response_dict.get("button_index")
        if button_index == self._button_index:
            self._is_on = response_dict.get("state", False)
            self.async_write_ha_state()
