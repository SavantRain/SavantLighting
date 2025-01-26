import asyncio
import logging, time
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.components.climate.const import FAN_AUTO,FAN_HIGH,FAN_LOW,FAN_MEDIUM
from homeassistant.const import ATTR_TEMPERATURE,UnitOfTemperature
from homeassistant.core import HomeAssistant

from .floor_heating import SavantFloorHeating
from .fresh_air import SavantFreshAirAC
from .const import DOMAIN
from .command_helper import ClimateCommand
from .send_command import *

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

SUPPORTED_HVAC_MODES = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.AUTO, HVACMode.DRY]
SUPPORTED_FAN_MODES = [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]

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
    
    floor_heatings = [
        SavantFloorHeating(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "floor_heating"
    ]
    
    async_add_entities(climates + floor_heatings, update_before_add=True)

class SavantClimate(ClimateEntity):
    """Representation of a Savant Climate (AC)."""

    def __init__(self, name, module_address, loop_address, host, port, tcp_manager):
        """Initialize the climate entity."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._state = HVACMode.OFF
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
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

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
        return UnitOfTemperature.CELSIUS
    
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
        if hvac_mode in SUPPORTED_HVAC_MODES:
            self._state = hvac_mode
            command = self.command.hvac_mode(hvac_mode)
            for cmd in command:
                await self.tcp_manager.send_command(cmd)
                await asyncio.sleep(0.5)
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        if fan_mode in SUPPORTED_FAN_MODES:
            self._fan_mode = fan_mode
            command = self.command.fan_mode(fan_mode)
            await self.tcp_manager.send_command(command)
            await asyncio.sleep(0.5)
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            self._target_temperature = temperature
            command = self.command.temperature(f"temp:{temperature}")
            await self.tcp_manager.send_command(command)
            await asyncio.sleep(0.5)
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


    # async def _get_state_from_device(self):
    #     """Query the device for its current state."""
    #     hex_command = self._query_to_hex("get_state")
    #     response, is_online = await self.tcp_manager.send_command(hex_command)
    #     return response

    def update_state(self, response_dict):
        print('空调收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']
        if response_dict['hvac_type'] == "hvac_01":
            if response_dict["data1"] == 0x00:
                device._state = HVACMode.OFF
        elif response_dict['hvac_type'] == "hvac_02":
            if response_dict["data1"] == 0x01:
                device._state = HVACMode.COOL
            elif response_dict["data1"] == 0x08:
                device._state = HVACMode.HEAT
            elif response_dict["data1"] == 0x04:
                device._state = HVACMode.AUTO
            elif response_dict["data1"] == 0X02:
                device._state = HVACMode.DRY
        elif response_dict['hvac_type'] == "hvac_04":
            device._target_temperature = response_dict["data1"]
        elif response_dict['hvac_type'] == "hvac_09":
            device._current_temperature = response_dict["data1"]
        elif response_dict['hvac_type'] == "hvac_03":
            if response_dict["data1"] == 0x04:
                device._fan_mode = FAN_LOW
            elif response_dict["data1"] == 0x02:
                device._fan_mode = FAN_MEDIUM
            elif response_dict["data1"] == 0x01:
                device._fan_mode = FAN_HIGH
            elif response_dict["data1"] == 0x00:
                device._fan_mode = FAN_AUTO
        device.async_write_ha_state()
