import logging, time
from datetime import timedelta
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_AUTO,
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

SUPPORTED_HVAC_MODES = [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_AUTO]
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
        
    # async def async_set_hvac_mode(self, hvac_mode):
    #     """Set the HVAC mode."""
    #     if hvac_mode in SUPPORTED_HVAC_MODES:
    #         self._state = hvac_mode
    #         await self._send_state_to_device(hvac_mode)
    #         self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        if hvac_mode in SUPPORTED_HVAC_MODES:
            self._state = hvac_mode
            hex_command = self._command_to_hex(hvac_mode)
            if isinstance(hex_command, tuple):
                # 如果是两条指令，依次发送
                response_1, is_online_1 = await self.tcp_manager.send_command(hex_command[0])
                response_2, is_online_2 = await self.tcp_manager.send_command(hex_command[1])
                # 这里可以根据实际需求对两次响应进行处理，比如检查是否都成功等
            else:
                response, is_online = await self.tcp_manager.send_command(hex_command)
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode."""
        if fan_mode in SUPPORTED_FAN_MODES:
            self._fan_mode = fan_mode
            await self._send_state_to_device(fan_mode)
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            self._target_temperature = temperature
            await self._send_state_to_device(f"temp:{temperature}")
            self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for this climate device."""
        try:
            response = await self._get_state_from_device()
            if response:
                self._parse_device_state(response)
        except Exception as e:
            _LOGGER.error(f"Error updating state: {e}")

    def update_state(self, response_dict):
        print('空调收到状态响应: ' + str(response_dict).replace('\\x', ''))
    
    
    
    
    
    
    # 以下根据light调整代码
    async def _send_state_to_device(self, command):
        """Send the command to the device."""
        hex_command = self._command_to_hex(command)
        for command in hex_command:
            await self.tcp_manager.send_command(command)
            time.sleep(500)

    async def _get_state_from_device(self):
        """Query the device for its current state."""
        hex_command = self._query_to_hex("get_state")
        response, is_online = await self.tcp_manager.send_command(hex_command)
        return response

    def _command_to_hex(self, command):
        """将'开'和'关'的命令转换为十六进制格式"""
        #指令第二个字节为IP的最后一位，如192.168.1.230，将230转化为十六进制E6在指令中进行传输
        host_hex = f"AC{int(self._host.split('.')[-1]):02X}0010"
        module_hex = f"{int(self._module_address):02X}"
        loop_hex = f"{int(self._loop_address):02X}"
        loop_hex_value = int(loop_hex, 16)
        
        #空调地址为32-47
        command_hex = []
        if command == HVAC_MODE_OFF:
            loop_hex_modeaddress = loop_hex_value * 9 - 287
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex = f"{loop_hex_original}000400002020CA"
        elif command == HVAC_MODE_COOL:
            #开机模式控制需要连续发送两条指令
            # 第一条指令用于空调开机
            loop_hex_modeaddress = loop_hex_value * 9 - 287
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex.append(f"{loop_hex_original}000401002020CA")
            # command_hex_1 = f"{loop_hex_original}000401002020CA"
            # 第二条指令用于开启制冷
            loop_hex_modeaddress = loop_hex_value * 9 - 286
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex.append(f"{loop_hex_original}000401002020CA")
            # command_hex_2 = f"{loop_hex_original}000401002020CA"
            return command_hex
        elif command == HVAC_MODE_HEAT:
            # 第一条指令用于空调开机
            loop_hex_modeaddress = loop_hex_value * 9 - 287
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex_1 = f"{loop_hex_original}000401002020CA"
            # 第二条指令用于开启制热
            loop_hex_modeaddress = loop_hex_value * 9 - 286
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex_2 = f"{loop_hex_original}000408002020CA"
            return command_hex_1, command_hex_2
        elif command == HVAC_MODE_AUTO:
            # 第一条指令用于空调开机
            loop_hex_modeaddress = loop_hex_value * 9 - 287
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex_1 = f"{loop_hex_original}000401002020CA"
            # 第二条指令用于开启通风
            loop_hex_modeaddress = loop_hex_value * 9 - 286
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex_2 = f"{loop_hex_original}000404002020CA"
            return command_hex_1, command_hex_2
        elif command.startswith("temp:"):
            #温度下发指令范围16-35°
            temperature_str = command.split(":")[1]
            temperature_hex = f"{int(float(temperature_str)):02X}"
            loop_hex_modeaddress = loop_hex_value * 9 - 284
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex = f"{loop_hex_original}0004{temperature_hex}002020CA"
        elif command == "low":
            loop_hex_modeaddress = loop_hex_value * 9 - 285
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex = f"{loop_hex_original}000404002020CA"
        elif command == "medium":
            loop_hex_modeaddress = loop_hex_value * 9 - 285
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex = f"{loop_hex}000402002020CA"
        elif command == "high":
            loop_hex_modeaddress = loop_hex_value * 9 - 285
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex = f"{loop_hex}000401002020CA"
        elif command == "auto":
            loop_hex_modeaddress = loop_hex_value * 9 - 285
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_hex = f"{loop_hex}000400002020CA"
        else:
            command_hex = ""

        if isinstance(command_hex, tuple):
            host_bytes_1 = bytes.fromhex(host_hex)
            module_bytes_1 = bytes.fromhex(module_hex)
            command_bytes_1 = bytes.fromhex(command_hex[0])
            command_1 = host_bytes_1 + module_bytes_1 + command_bytes_1

            host_bytes_2 = bytes.fromhex(host_hex)
            module_bytes_2 = bytes.fromhex(module_hex)
            command_bytes_2 = bytes.fromhex(command_hex[1])
            command_2 = host_bytes_2 + module_bytes_2 + command_bytes_2

            return command_1, command_2
        else:
            host_bytes = bytes.fromhex(host_hex)
            module_bytes = bytes.fromhex(module_hex)
            command_bytes = bytes.fromhex(command_hex)
            command = host_bytes + module_bytes + command_bytes

            return command

    def _query_to_hex(self, command):
        """Convert a query to its hexadecimal representation."""
        host_hex = f"{int(self._host.split('.')[-1]):02X}"
        module_hex = f"{int(self._module_address):02X}"
        command_hex = '01000108CA'

        host_bytes = bytes.fromhex(host_hex)
        module_bytes = bytes.fromhex(module_hex)
        command_bytes = bytes.fromhex(command_hex)
        query_command = host_bytes + module_bytes + command_bytes

        return query_command

    def _parse_device_state(self, response):
        """Parse the state from the device's response."""
        if len(response) >= 12:
            loop_hex = f"{int(self._loop_address):02X}"
            mode_indicator = response[5]
            temperature_indicator = response[7]
            fan_mode_indicator = response[9]

            if mode_indicator == 0x01:
                self._state = HVAC_MODE_OFF
            elif mode_indicator == 0x02:
                self._state = HVAC_MODE_COOL
            elif mode_indicator == 0x03:
                self._state = HVAC_MODE_HEAT
            elif mode_indicator == 0x03:
                self._state = HVAC_MODE_AUTO

            self._current_temperature = float(int(temperature_indicator, 16) / 10)

            if fan_mode_indicator == 0x01:
                self._fan_mode = "low"
            elif fan_mode_indicator == 0x02:
                self._fan_mode = "medium"
            elif fan_mode_indicator == 0x03:
             self._fan_mode = "high"
            elif fan_mode_indicator == 0x04:
                self._fan_mode = "auto"

        else:
            _LOGGER.error("Invalid device response length: {len(response)}")
