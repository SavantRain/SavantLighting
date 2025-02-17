import asyncio
import logging
from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from datetime import timedelta
from .const import DOMAIN
from .command_helper import CurtainCommand
from .send_command import *

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Fresh Air entities from a config entry."""
    config = hass.data[DOMAIN].get(entry.entry_id, {})
    devices = config.get("devices", [])
    
    curtains = [
        SavantFreshCurtain(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "curtain"
    ]
    async_add_entities(curtains, update_before_add=True)


class SavantFreshCurtain(CoverEntity):
    """Representation of an automatic curtain with open, close, and position control."""

    def __init__(self, name, module_address, loop_address, host, port, tcp_manager):
        """Initialize the fresh air fan."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._position = 0  # Initial position is fully closed (0%)
        self._state = STATE_OFF  # Curtain is initially closed
        self._attr_is_closed = True
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("curtain", self.update_state)
        self.command = CurtainCommand(host, module_address, loop_address)

    @property
    def unique_id(self):
        """Return a unique ID for this curtain."""
        return f"{self._module_address}_{self._loop_address}_curtain"

    @property
    def is_open(self):
        """Return if the curtain is fully open."""
        return self._position == 100

    @property
    def current_cover_position(self):
        """Return the current position of the curtain (0 - 100%)."""
        return self._position
    
    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_curtain")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Curtain Model",
        }

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return CoverEntityFeature.SET_POSITION | CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    async def async_open_cover(self, **kwargs):
        """Open the curtain completely."""
        self._position = 100
        await self._send_command("open")
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        """Close the curtain completely."""
        self._position = 0
        await self._send_command("close")
        self.async_write_ha_state()

    async def async_set_cover_position(self, position: int, **kwargs):
        """Set the curtain's position (0-100%)."""
        self._position = position
        await self._send_command(f"set_position:{position}")
        self.async_write_ha_state()

    async def _send_command(self, command: str):
        host_hex = f"AC{int(self._host.split('.')[-1]):02X}0010"
        module_hex = f"{int(self._module_address):02X}"
        loop_hex = f"{int(self._loop_address):02X}"
        
        base_command = bytes.fromhex(host_hex + module_hex + loop_hex)

        if command == "open":
            hex_command = base_command + b'\x00\x04\x64\x00\x00\x00\xCA'
        elif command == "close":
            hex_command = base_command + b'\x00\x04\x00\x00\x00\x00\xCA'
        elif command.startswith("set_position:"):
            position = int(command.split(":")[1])
            position_hex = f"{position:02X}"
            hex_command = base_command + b'\x00\x04' + bytes.fromhex(position_hex) + b'\x00\x00\x00\xCA'
        else:
            raise ValueError("Unsupported command")

        await self.tcp_manager.send_command(hex_command)
        _LOGGER.debug(f"Sent command to curtain: {command}")

    def update_state(self, response_dict):
        """Update the state of the curtain based on the response from the device."""
        print('窗帘收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']

        if response_dict["data1"] == 0x00:
            device._state = STATE_OFF
            device._position = 0
        else:
            device._state = STATE_ON
            device._position = response_dict["data1"]

        device._attr_is_closed = device._position == 0 
        device.async_write_ha_state() 
