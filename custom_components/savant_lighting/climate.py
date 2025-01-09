import asyncio
import logging, time
from datetime import timedelta
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_AUTO,
    HVAC_MODE_DRY,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .command_helper import ClimateCommand
from .send_command import *


_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

SUPPORTED_HVAC_MODES = [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_AUTO, HVAC_MODE_DRY]
SUPPORTED_FAN_MODES = ["low", "medium", "high", "auto"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Climate entities from a config entry."""
    config = hass.data[DOMAIN].get(entry.entry_id, {})
    devices = config.get("devices", [])
    
    climates = [
        SavantClimate(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "climate"
    ]
    async_add_entities(climates, update_before_add=True)

class SavantClimate(ClimateEntity):
    """Representation of a Savant Climate (AC)."""

    def __init__(self, name, module_address, loop_address, host, port, tcp_manager):
        """Initialize the climate entity."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._state = HVAC_MODE_OFF
        self._current_temperature = 24.0
        self._target_temperature = 24.0
        self._fan_mode = "auto"
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("climate", self.update_state)
        self.command = ClimateCommand(host,module_address,loop_address)
        
    async def async_added_to_hass(self):
        self.hass.async_create_task(self.async_update())
        self.async_write_ha_state()
        
    @property
    def unique_id(self):
        """Return a unique ID for this climate entity."""
        return f"{self._module_address}_{self._loop_address}_climate"
    
    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

    @property
    def hvac_modes(self):
        """Return the supported HVAC modes."""
        return SUPPORTED_HVAC_MODES

    @property
    def fan_modes(self):
        """Return the supported fan modes."""
        return SUPPORTED_FAN_MODES

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS
    
    @property 
    def target_temperature_step(self): 
        """Return the supported step of target temperature.""" 
        return 1
    @property 
    def min_temp(self): 
        """Return the minimum temperature.""" 
        return 16 
    @property 
    def max_temp(self): 
        """Return the maximum temperature.""" 
        return 35
    
    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        return self._state

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def fan_mode(self):
        """Return the current fan mode."""
        return self._fan_mode

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Climate Model",
        }

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        if hvac_mode in SUPPORTED_HVAC_MODES:
            self._state = hvac_mode
            await self._send_state_to_device(hvac_mode,'hvac_mode')
            self.async_write_ha_state()


    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode."""
        if fan_mode in SUPPORTED_FAN_MODES:
            self._fan_mode = fan_mode
            await self._send_state_to_device(fan_mode,'fan_mode')
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            self._target_temperature = temperature
            await self._send_state_to_device(f"temp:{temperature}", 'temperature')
            self.async_write_ha_state()

    async def async_update(self):
        return
        # # self._state = True
        # """Fetch new state data for this climate device."""
        # try:
        #     response = await self._get_state_from_device()
        #     if response:
        #         self._parse_device_state(response)
        # except Exception as e:
        #     _LOGGER.error(f"Error updating state: {e}")

    # 以下根据light调整代码
    async def _send_state_to_device(self, command, command_type):
        """Send the command to the device."""
        commands = self._command_to_hex(command, command_type)
        for cmd in commands:
            await self.tcp_manager.send_command(cmd)
            await asyncio.sleep(0.5) 

    # async def _get_state_from_device(self):
    #     """Query the device for its current state."""
    #     hex_command = self._query_to_hex("get_state")
    #     response, is_online = await self.tcp_manager.send_command(hex_command)
    #     return response
    def _command_to_hex(self, command, command_type):
        """将控制命令转换为十六进制格式"""
        host_hex = f"AC{int(self._host.split('.')[-1]):02X}0010"
        module_hex = f"{int(self._module_address):02X}"
        loop_hex = f"{int(self._loop_address):02X}"
        loop_hex_value = int(loop_hex, 16)

        command_list = []
        if command_type == "hvac_mode":
            if command ==  HVAC_MODE_OFF:
                loop_hex_modeaddress = loop_hex_value * 9 - 287
                loop_hex_original = f"{loop_hex_modeaddress:02X}"
                command_list.append(f"{loop_hex_original}000400002020CA")
            elif command == HVAC_MODE_COOL:
                command_list.append(f"{loop_hex_value * 9 - 287:02X}000401000000CA")
                command_list.append(f"{loop_hex_value * 9 - 286:02X}000405000000CA")
            elif command == HVAC_MODE_HEAT:
                command_list.append(f"{loop_hex_value * 9 - 287:02X}000401000000CA")
                command_list.append(f"{loop_hex_value * 9 - 286:02X}000408002020CA")
            elif command == HVAC_MODE_AUTO:
                command_list.append(f"{loop_hex_value * 9 - 287:02X}000401000000CA")
                command_list.append(f"{loop_hex_value * 9 - 286:02X}000404000000CA")
            elif command == HVAC_MODE_DRY:
                command_list.append(f"{loop_hex_value * 9 - 287:02X}000401000000CA")
                command_list.append(f"{loop_hex_value * 9 - 286:02X}000402000000CA")
        elif command_type == "temperature":
            if command.startswith("temp:"):
                temperature_str = command.split(":")[1]
                temperature_hex = f"{int(float(temperature_str)):02X}"
                command_list.append(f"{loop_hex_value * 9 - 284:02X}0004{temperature_hex}000000CA")
        elif command_type == "fan_mode":
            if command in ["low", "medium", "high", "auto"]:
                fan_speed_map = {"low": "04", "medium": "02", "high": "01", "auto": "00"}
                command_list.append(f"{loop_hex_value * 9 - 285:02X}0004{fan_speed_map[command]}000000CA")
        else:
            raise ValueError("Unsupported command")
        
        host_bytes = bytes.fromhex(host_hex)
        module_bytes = bytes.fromhex(module_hex)
        return [host_bytes + module_bytes + bytes.fromhex(cmd) for cmd in command_list]

    # def _query_to_hex(self, command):
    #     """Convert a query to its hexadecimal representation."""
    #     host_hex = f"{int(self._host.split('.')[-1]):02X}"
    #     module_hex = f"{int(self._module_address):02X}"
    #     command_hex = '01000108CA'

    #     host_bytes = bytes.fromhex(host_hex)
    #     module_bytes = bytes.fromhex(module_hex)
    #     command_bytes = bytes.fromhex(command_hex)
    #     query_command = host_bytes + module_bytes + command_bytes

    #     return query_command

    def update_state(self, response_dict):
        print('空调收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']
        if response_dict['hvac_type'] == "hvac_01":
            if response_dict["data1"] == 0x00:
                device._state = HVAC_MODE_OFF
        elif response_dict['hvac_type'] == "hvac_02":
            if response_dict["data1"] == 0x01:
                device._state = HVAC_MODE_COOL
            elif response_dict["data1"] == 0x08:
                device._state = HVAC_MODE_HEAT
            elif response_dict["data1"] == 0x04:
                device._state = HVAC_MODE_AUTO
            elif response_dict["data1"] == 0X02:
                device._state = HVAC_MODE_DRY
        elif response_dict['hvac_type'] == "hvac_04":
            device._target_temperature = response_dict["data1"]
        elif response_dict['hvac_type'] == "hvac_09":
            device._current_temperature = response_dict["data1"]
        elif response_dict['hvac_type'] == "hvac_03":
            if response_dict["data1"] == 0x04:
                device._fan_mode = "low"
            elif response_dict["data1"] == 0x02:
                device._fan_mode = "medium"
            elif response_dict["data1"] == 0x01:
                device._fan_mode = "high"
            elif response_dict["data1"] == 0x00:
                device._fan_mode = "auto"
        device.async_write_ha_state()
    
    # def _parse_device_state(self, response):
    #     """Parse the state from the device's response."""
    #     if len(response) >= 12:
    #         loop_hex = f"{int(self._loop_address):02X}"
    #         mode_indicator = response[5]
    #         temperature_indicator = response[7]
    #         fan_mode_indicator = response[9]

    #         if mode_indicator == 0x01:
    #             self._state = HVAC_MODE_OFF
    #         elif mode_indicator == 0x02:
    #             self._state = HVAC_MODE_COOL
    #         elif mode_indicator == 0x03:
    #             self._state = HVAC_MODE_HEAT
    #         elif mode_indicator == 0x03:
    #             self._state = HVAC_MODE_AUTO

    #         self._current_temperature = float(int(temperature_indicator, 16) / 10)

    #         if fan_mode_indicator == 0x01:
    #             self._fan_mode = "low"
    #         elif fan_mode_indicator == 0x02:
    #             self._fan_mode = "medium"
    #         elif fan_mode_indicator == 0x03:
    #          self._fan_mode = "high"
    #         elif fan_mode_indicator == 0x04:
    #             self._fan_mode = "auto"

    #     else:
    #         _LOGGER.error("Invalid device response length: {len(response)}")
