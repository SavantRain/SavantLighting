import asyncio
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from datetime import timedelta

from .const import DOMAIN
from .send_command import *

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Fresh Air entities from a config entry."""
    config = hass.data[DOMAIN].get(entry.entry_id, {})
    devices = config.get("devices", [])
    
    person_sensors = [
        SavantPersonSensor(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "person_sensor"
    ]
    async_add_entities(person_sensors, update_before_add=True)


class SavantPersonSensor(BinarySensorEntity):
    """Representation of a human presence sensor."""

    def __init__(self, name, module_address, loop_address, host, port, tcp_manager):
        """Initialize the human presence sensor."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._state = STATE_OFF  # 初始状态为“没有人”
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("person_sensor", self.update_state)

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{self._module_address}_{self._loop_address}_person_sensor"

    @property
    def is_on(self):
        """Return true if human is detected (sensor is 'on')."""
        return self._state == STATE_ON

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_person_sensor")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Human Presence Sensor Model",
        }

    async def async_update(self):
        """Fetch new state data for this sensor."""
        try:
            # 这里我们假设获取到人体传感器的状态
            response = await self._get_sensor_state()
            self._state = response.get("state", STATE_OFF)
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"Error updating sensor state: {e}")

    async def _get_sensor_state(self):
        """获取传感器的状态，模拟从设备获取信息的过程。"""
        # 模拟设备返回的状态，根据实际协议修改
        response = {"state": STATE_OFF}  # 假设返回有人
        return response

    def update_state(self, response_dict):
        """Update the state of the sensor based on the response."""
        print('感应收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']
        if response_dict["data1"] == 0x01:  
            device._state = STATE_ON
        elif response_dict["data1"] == 0x02:  
            device._state = STATE_OFF 

        # _LOGGER.debug(f"Human Presence Sensor received state response: {response_dict}")
        # self._state = response_dict.get("state", STATE_OFF)
        device.async_write_ha_state()