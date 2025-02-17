import logging
from datetime import timedelta
from homeassistant.components.switch import SwitchEntity
from .command_helper import SwitchSceneCommand
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

class SavantSwitchScene(SwitchEntity):

    def __init__(self, name, module_address, loop_address, scene_number, host, port, tcp_manager):
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._scene_number = scene_number
        self._host = host
        self._port = port
        self._is_on = False
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("scene_switch", self.update_state)
        self.command = SwitchSceneCommand(host, scene_number)
        

    @property
    def unique_id(self):
        """Return a unique ID for this switch button."""
        return f"{self._module_address}_{self._loop_address}_{self._scene_number}_scene_switch"

    @property
    def is_on(self):
        """Return true if the button is on."""
        return self._is_on

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_scene_switch")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Switch Scene Model",
        }
        
    async def async_turn_on(self, **kwargs):
        self._state = True
        await self.tcp_manager.send_command(self.command.turnonoff("on"))

    async def async_turn_off(self, **kwargs):
        self._state = True
        await self.tcp_manager.send_command(self.command.turnonoff("off"))
        
    def update_state(self, response_dict):
        print('开关收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']
        device._state = self._parse_device_state(response_dict['response_str'])
        device.async_write_ha_state()