import asyncio
import logging, time
from datetime import timedelta
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.components.climate.const import FAN_AUTO,FAN_HIGH,FAN_LOW,FAN_MEDIUM
from homeassistant.const import ATTR_TEMPERATURE,UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .command_helper import ClimateCommand
from .send_command import *

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

SUPPORTED_HVAC_MODES = [HVACMode.OFF, HVACMode.HEAT]
SUPPORTED_FAN_MODES = [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]

class SavantFloorHeating(ClimateEntity):
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
        self.tcp_manager.register_callback("floor_heating", self.update_state)
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
            "model": "Floor Heating Model",
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

    def update_state(self, response_dict):
        print('地暖收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']
        device.async_write_ha_state()
