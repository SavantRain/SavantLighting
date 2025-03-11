import logging
from datetime import timedelta
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .tcp_manager import *
from .const import DOMAIN
from .command_helper import SwitchCommand

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

class SavantEnergySwitch(SwitchEntity):
    """Representation of a Savant Switch with Energy Monitoring."""

    def __init__(self, name, module_address, loop_address, host, port, tcp_manager):
        """Initialize the switch."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._state = False
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("switch_with_energy", self.update_state)
        self.command = SwitchCommand(host, module_address, loop_address)

    @property
    def unique_id(self):
        """Return a unique ID for this switch."""
        return f"{self._module_address}_{self._loop_address}_switch_with_energy"

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_switch_with_energy")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Switch with Energy Monitor Model",
        }

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug(f"Turning on {self._attr_name}")
        self._state = True
        await self.tcp_manager.send_command(self.command.turnonoff("on"))

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug(f"Turning off {self._attr_name}")
        self._state = False
        await self.tcp_manager.send_command(self.command.turnonoff("off"))

    def get_sensor_entity(self, sensor_unique_id):
        entity_registry = async_get_entity_registry(self.hass)
        entity_entry = None
        for entry in entity_registry.entities.values():
            if entry.unique_id == sensor_unique_id:
                entity_entry = entry
                break
        entity_id = entity_entry.entity_id
        sensor = self.hass.data['sensor'].get_entity(entity_id)
        return sensor

    def update_state(self, response_dict):
        _LOGGER.debug('Switch state update received: %s', response_dict)
        device = response_dict['device']
        if response_dict["data1"] == 0x00:
            device._state = False
        else:
            device._state = True
        device.async_write_ha_state()

        sensor = self.get_sensor_entity(f"{self._module_address}_{self._loop_address}_switch_with_energy_voltage_sensor")
        sensor._state = 1.0
        sensor.async_write_ha_state()

        sensor = self.get_sensor_entity(f"{self._module_address}_{self._loop_address}_switch_with_energy_current_sensor")
        sensor._state = 1.0
        sensor.async_write_ha_state()

        sensor = self.get_sensor_entity(f"{self._module_address}_{self._loop_address}_switch_with_energy_power_sensor")
        sensor._state = 1.0
        sensor.async_write_ha_state()

    def _parse_response(self, response_str):
        pass
