import asyncio
import logging
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from datetime import timedelta

from .const import DOMAIN
from .command_helper import FanCommand
from .send_command import *

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

SUPPORTED_SPEEDS = ["low", "medium", "high", "auto"]

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
        self._state = False
        self._speed = "auto"  # Default speed
        self._speed_percentage = 0
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("fresh_air", self.update_state)
        self.command = FanCommand(host, module_address, loop_address)

    @property
    def unique_id(self):
        """Return a unique ID for this fan."""
        return f"{self._module_address}_{self._loop_address}_fresh_air"

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    @property
    def speed(self):
        """Return the current speed of the fan."""
        return self._speed
    
    @property
    def percent(self):
        return self._speed_percentage
    
    @property
    def speed_list(self):
        """Return the list of supported speeds."""
        return SUPPORTED_SPEEDS

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF | FanEntityFeature.SET_SPEED

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Fresh Air Model",
        }

    async def async_turn_on(self, percentage, preset_mode, **kwargs):
        """Turn the fan on."""
        self._state = True
        self._speed = self._map_speed_to_percent(50)
        hex_command = self._command_to_hex("on", self._speed)
        await self.tcp_manager.send_command_list(hex_command)
        await asyncio.sleep(1)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the fan off."""
        self._state = False
        hex_command = self._command_to_hex("off")
        await self.tcp_manager.send_command_list(hex_command)
        await asyncio.sleep(1)
        self.async_write_ha_state()

    async def async_set_percentage(self, **kwargs):
        speed = kwargs['percentage']
        self._speed = self._map_speed_to_percent(speed)
        if self._state:
            hex_command = self._command_to_hex("on", self._speed)
            await self.tcp_manager.send_command_list(hex_command)
            await asyncio.sleep(1)
        self.async_write_ha_state()

    async def async_set_speed(self, speed):
        """Set the speed of the fan based on the percentage."""
        self._speed = speed
        self.async_write_ha_state()

    def _map_speed_to_percent(self, speed) -> str:
        """Map the speed percentage to the supported speed levels."""
        if 1 <= speed <= 30:
            return "low"
        elif 31 <= speed <= 70:
            return "medium"
        elif 71 <= speed <= 100:
            return "high"
        elif speed == 0:
            return "speed_off"
        else:
            return "auto"  # Default to auto if the speed is out of range

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
            elif speed == "speed_off":
                command_list.append(f"{loop_hex_value * 9 - 281:02X}000401000000CA")
                command_list.append(f"{loop_hex_value * 9 - 280:02X}000400000000CA")
        elif action == "off":
            command_list.append(f"{loop_hex_value * 9 - 281:02X}000400000000CA")
        else:
            raise ValueError("Unsupported action")
        
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
                device._speed = 'low'
                device._speed_percentage = 20
            elif response_dict["data1"] == 0x02:
                device._speed = 'medium'
                device._speed_percentage = 50
            elif response_dict["data1"] == 0x03:
                device._speed = 'high'
                device._speed_percentage = 80
            elif response_dict["data1"] == 0x00:
                device._speed = 'auto'
                device._speed_percentage = 0
        device.async_write_ha_state()
        print(device._speed)
        print(device._speed_percentage)
        print('')
        # """Update the state of the fan based on the response."""
        # _LOGGER.debug(f"Fresh Air Fan received state response: {response_dict}")
        # self._is_on = response_dict.get("state") == STATE_ON
        # self._speed = response_dict.get("speed", self._speed)

        