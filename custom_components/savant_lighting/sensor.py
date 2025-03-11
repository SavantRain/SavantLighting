import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .tcp_manager import *
from .const import DOMAIN
from .command_helper import SwitchCommand
from .switch_8_button import SavantSwitch8Button
from .switch_scene import SavantSwitchScene

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Light entities from a config entry."""
    config = hass.data[DOMAIN].get(entry.entry_id, {})
    devices = config.get("devices", [])
    tcp_manager=config["tcp_manager"]
    entities = []
    for device in devices:
        if device["type"] == "switch_with_energy":
            module_address = device["module_address"]
            loop_address = device["loop_address"]
            name = device["name"]
            # Create and append voltage, current, and power sensors
            entities.append(SavantVoltageSensor(name, module_address, loop_address, tcp_manager))
            entities.append(SavantCurrentSensor(name, module_address, loop_address, tcp_manager))
            entities.append(SavantPowerSensor(name, module_address, loop_address, tcp_manager))
            entities.append(SavantEnergySensor(name, module_address, loop_address, tcp_manager))

    async_add_entities(entities, update_before_add=True)

class SavantVoltageSensor(SensorEntity):
    """Representation of a voltage sensor."""

    def __init__(self, name, module_address, loop_address, tcp_manager):
        """Initialize the voltage sensor."""
        self._attr_name = f"{name} 电压"
        self._module_address = module_address
        self._loop_address = loop_address
        self._state = 0.0
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("switch_with_energy_voltage_sensor", self.update_state)

    @property
    def unique_id(self):
        """Return a unique ID for this voltage sensor."""
        return f"{self._module_address}_{self._loop_address}_switch_with_energy_voltage_sensor"

    @property
    def state(self):
        """Return the current voltage."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "V"

    @property
    def icon(self):
        return "mdi:flash"

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_switch_with_energy")},
        }

    def update_state(self, response_dict):
        self._state = response_dict.get("voltage", 0.0)
        self.async_write_ha_state()

class SavantCurrentSensor(SensorEntity):
    """Representation of a current sensor."""

    def __init__(self, name, module_address, loop_address, tcp_manager):
        """Initialize the current sensor."""
        self._attr_name = f"{name} 电流"
        self._module_address = module_address
        self._loop_address = loop_address
        self._state = 0.0
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("switch_with_energy_current_sensor", self.update_state)

    @property
    def unique_id(self):
        """Return a unique ID for this current sensor."""
        return f"{self._module_address}_{self._loop_address}_switch_with_energy_current_sensor"

    @property
    def state(self):
        """Return the current."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "A"

    @property
    def icon(self):
        return "mdi:current-ac"

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_switch_with_energy")},
        }

    def update_state(self, response_dict):
        self._state = response_dict.get("current", 0.0)
        self.async_write_ha_state()

class SavantPowerSensor(SensorEntity):
    """Representation of a power sensor."""

    def __init__(self, name, module_address, loop_address, tcp_manager):
        """Initialize the power sensor."""
        self._attr_name = f"{name} 功率"
        self._module_address = module_address
        self._loop_address = loop_address
        self._state = 0.0
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("switch_with_energy_power_sensor", self.update_state)

    @property
    def unique_id(self):
        """Return a unique ID for this power sensor."""
        return f"{self._module_address}_{self._loop_address}_switch_with_energy_power_sensor"

    @property
    def state(self):
        """Return the power."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "W"

    @property
    def icon(self):
        return "mdi:power-plug"

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_switch_with_energy")},
        }

    def update_state(self, response_dict):
        self._state = response_dict.get("power", 0.0)
        self.async_write_ha_state()

class SavantEnergySensor(SensorEntity):
    """Representation of a power sensor."""

    def __init__(self, name, module_address, loop_address, tcp_manager):
        """Initialize the power sensor."""
        self._attr_name = f"{name} KW·h"
        self._module_address = module_address
        self._loop_address = loop_address
        self._state = 0.0
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("switch_with_energy_energy_sensor", self.update_state)

    @property
    def unique_id(self):
        """Return a unique ID for this energy sensor."""
        return f"{self._module_address}_{self._loop_address}_switch_with_energy_energy_sensor"

    @property
    def state(self):
        """Return the energy."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "KW·h"

    @property
    def icon(self):
        return "mdi:power-plug-battery"

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_switch_with_energy")},
        }

    def update_state(self, response_dict):
        self._state = response_dict.get("power", 0.0)
        self.async_write_ha_state()
