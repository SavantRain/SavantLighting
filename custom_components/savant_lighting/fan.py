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
        self._is_on = False
        self._speed = "auto"  # Default speed
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("fresh_air", self.update_state)
        self.command = FanCommand(host, module_address, loop_address)

    @property
    def unique_id(self):
        """Return a unique ID for this fan."""
        return f"{self._module_address}_{self._loop_address}_fresh_air"

    @property
    def is_on(self):
        """Return whether the fan is on or off."""
        return self._is_on

    @property
    def speed(self):
        """Return the current speed of the fan."""
        return self._speed

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

    async def async_turn_on(self, speed=None, **kwargs):
        """Turn the fan on."""
        self._is_on = True
        if speed:
            self._speed = self._map_speed_to_percent(speed)
        else:
            self._speed = "auto"  # Default to auto if no speed is specified
        hex_command = self._generate_hex_command("on", self._speed)
        await self.tcp_manager.send_command(hex_command)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the fan off."""
        self._is_on = False
        hex_command = self._generate_hex_command("off")
        await self.tcp_manager.send_command(hex_command)
        self.async_write_ha_state()

    async def async_set_speed(self, speed: str):
        """Set the speed of the fan based on the percentage."""
        self._speed = self._map_speed_to_percent(speed)
        if self._is_on:
            hex_command = self._generate_hex_command("on", self._speed)
            await self.tcp_manager.send_command(hex_command)
        self.async_write_ha_state()

    def _map_speed_to_percent(self, speed: str) -> str:
        """Map the speed percentage to the supported speed levels."""
        speed_percent = int(speed.strip('%'))  # Remove the '%' sign and convert to integer
        if 1 <= speed_percent <= 30:
            return "low"
        elif 31 <= speed_percent <= 60:
            return "medium"
        elif 61 <= speed_percent <= 100:
            return "high"
        else:
            return "auto"  # Default to auto if the speed is out of range

    def _generate_hex_command(self, action: str, speed: str = None) -> bytes:
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
        elif action == "off":
            command_list.append(f"{loop_hex_value * 9 - 281:02X}000400000000CA")
        else:
            raise ValueError("Unsupported action")

    def update_state(self, response_dict):
        """Update the state of the fan based on the response."""
        _LOGGER.debug(f"Fresh Air Fan received state response: {response_dict}")
        self._is_on = response_dict.get("state") == STATE_ON
        self._speed = response_dict.get("speed", self._speed)
        self.async_write_ha_state()