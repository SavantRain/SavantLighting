import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.climate.const import FAN_AUTO,FAN_HIGH,FAN_LOW,FAN_MEDIUM
from homeassistant.const import ATTR_TEMPERATURE,UnitOfTemperature
from datetime import timedelta

from .const import DOMAIN
from .command_helper import FreshAirCommand
from .send_command import *


_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

# 空调模式
SUPPORTED_SPEEDS = [FAN_AUTO,FAN_HIGH,FAN_LOW,FAN_MEDIUM]
SUPPORTED_MODES = [HVACMode.OFF, HVACMode.FAN_ONLY]

class SavantFreshAirAC(ClimateEntity):
    """Representation of a Savant Fresh Air AC."""

    def __init__(self, name, module_address, loop_address, host, port, tcp_manager):
        """Initialize the climate entity."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._state = STATE_OFF
        self._speed = FAN_AUTO
        self._attr_temperature_unit = None
        self._attr_current_temperature = None
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("fresh_air", self.update_state)
        self.command = FreshAirCommand(host,module_address,loop_address)

    @property
    def unique_id(self):
        """Return a unique ID for this AC."""
        return f"{self._module_address}_{self._loop_address}_fresh_air_ac"

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._attr_name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS
    
    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return SUPPORTED_MODES
    
    @property
    def hvac_mode(self):
        """Return the current HVAC mode (off, on, auto)."""
        return self._state
    
    @property
    def fan_modes(self):
        """Return the list of available fan modes (speeds)."""
        return SUPPORTED_SPEEDS
    
    @property
    def fan_mode(self):
        """Return the current fan mode (speed)."""
        return self._speed
    
    @property
    def supported_features(self):
        """Return the list of supported features."""
        return ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Fresh Air Model",
        }

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            self._state = hvac_mode
            hex_command = self._command_to_hex(STATE_OFF)
        elif hvac_mode == HVACMode.FAN_ONLY:
            self._state = hvac_mode
            self._speed = FAN_AUTO
            hex_command = self._command_to_hex(STATE_ON, self._speed)
        await self.tcp_manager.send_command_list(hex_command)
        self.async_write_ha_state()
            
    async def async_set_fan_mode(self, fan_mode: str):
        """Set the fan mode (speed)."""
        if fan_mode in SUPPORTED_SPEEDS:
            self._speed = fan_mode
            if self._state == HVACMode.FAN_ONLY:
                hex_command = self._command_to_hex(STATE_ON, self._speed)
                await self.tcp_manager.send_command_list(hex_command)
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"Unsupported fan mode: {fan_mode}")

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

        