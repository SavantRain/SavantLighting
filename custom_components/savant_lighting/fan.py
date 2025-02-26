import asyncio
import logging
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from datetime import timedelta

from .const import DOMAIN
from .command_helper import FreshAirCommand
from .send_command import *

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

SUPPORTED_PRESET_MODES = ["low", "medium", "high", "auto"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Fresh Air entities from a config entry."""
    config = hass.data[DOMAIN].get(entry.entry_id, {})
    devices = config.get("devices", [])

    fresh_airs = [
        SavantFreshAirFan(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "fresh_air"
    ]
    async_add_entities(fresh_airs, update_before_add=True)

class SavantFreshAirFan(FanEntity):
    """Representation of a Savant Fresh Air Fan."""

    def __init__(self, name, module_address, loop_address, host, port, tcp_manager):
        """Initialize the fresh air fan."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._state = True
        self._preset_mode = "auto"
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("fresh_air", self.update_state)
        self.command = FreshAirCommand(host, module_address, loop_address)

    @property
    def unique_id(self):
        """Return a unique ID for this fan."""
        return f"{self._module_address}_{self._loop_address}_fresh_air"

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    @property
    def preset_modes(self):
        """Return a list of supported preset modes."""
        return SUPPORTED_PRESET_MODES

    # @property
    # def preset_mode(self):
    #     """Return the current preset mode."""
    #     return self._preset_mode

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF | FanEntityFeature.PRESET_MODE

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_fresh_air")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Fresh Air Model",
        }

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs):
        """Turn the fan on."""
        self._state = True
        self._preset_mode = 'auto'
        hex_command = self._command_to_hex(STATE_ON, self._preset_mode)
        await self.tcp_manager.send_command_list(hex_command)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the fan off."""
        self._state = False
        hex_command = self._command_to_hex(STATE_OFF)
        await self.tcp_manager.send_command_list(hex_command)
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str):
        """Set the fan to a specific preset mode."""
        if preset_mode in SUPPORTED_PRESET_MODES:
            self._state = True
            self._preset_mode = preset_mode
            hex_command = self._command_to_hex(STATE_ON, preset_mode)
            await self.tcp_manager.send_command_list(hex_command)
            self.async_write_ha_state()

    def _command_to_hex(self, action: str, speed: str = None) -> bytes:
        """将控制命令转换为十六进制格式"""
        host_hex = f"AC{int(self._host.split('.')[-1]):02X}0010"
        module_hex = f"{int(self._module_address):02X}"
        loop_hex = f"{int(self._loop_address):02X}"
        loop_hex_value = int(loop_hex, 16)

        command_list = []
        if action == "on":
            if speed == "high":
                command_list.append(f"{loop_hex_value * 9 - 281:02X}000401000000CA")
                command_list.append(f"{loop_hex_value * 9 - 280:02X}000403000000CA")
            elif speed == "medium":
                command_list.append(f"{loop_hex_value * 9 - 281:02X}000401000000CA")
                command_list.append(f"{loop_hex_value * 9 - 280:02X}000402000000CA")
            elif speed == "low":
                command_list.append(f"{loop_hex_value * 9 - 281:02X}000401000000CA")
                command_list.append(f"{loop_hex_value * 9 - 280:02X}000401000000CA")
            elif speed == "auto":
                ##########请确认下此代码是否正确，之前判断的是speed_off,但下面已经有off了，但没有auto ############
                command_list.append(f"{loop_hex_value * 9 - 281:02X}000401000000CA")
                command_list.append(f"{loop_hex_value * 9 - 280:02X}000400000000CA")
        elif action == "off":
            command_list.append(f"{loop_hex_value * 9 - 281:02X}000400000000CA")

        host_bytes = bytes.fromhex(host_hex)
        module_bytes = bytes.fromhex(module_hex)
        return [host_bytes + module_bytes + bytes.fromhex(cmd) for cmd in command_list]

    def update_state(self, response_dict):
        print('新风收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']
        if response_dict['hvac_type'] == "hvac_07":
            if response_dict["data1"] == 0x00:
                device._state = False
        elif response_dict['hvac_type'] == "hvac_08":
            device._state = True
            if response_dict["data1"] == 0x01:
                device._preset_mode = 'low'
            elif response_dict["data1"] == 0x02:
                device._preset_mode = 'medium'
            elif response_dict["data1"] == 0x03:
                device._preset_mode = 'high'
            elif response_dict["data1"] == 0x00:
                device._preset_mode = 'auto'
        device.async_write_ha_state()
        print(device._preset_mode)

