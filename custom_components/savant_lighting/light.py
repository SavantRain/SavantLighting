import logging
from datetime import timedelta
from homeassistant.components.light import LightEntity, ColorMode, SUPPORT_COLOR
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .command_helper import LightCommand
from .send_command import *

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Light entities from a config entry."""
    config = hass.data[DOMAIN].get(entry.entry_id, {})
    devices = config.get("devices", [])

    lights = [
        SavantLight(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            gradient_time=device["gradient_time"],
            host=device["host"],
            port=device["port"],
            sub_device_type=device["sub_device_type"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "light"
    ]
    async_add_entities(lights, update_before_add=True)

class SavantLight(LightEntity):
    """Representation of a Savant Light."""

    def __init__(self, name, module_address, loop_address, gradient_time, host, port, sub_device_type, tcp_manager):
        """Initialize the Savant Light."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._gradient_time = gradient_time
        self._host = host
        self._port = port
        self._sub_device_type = sub_device_type
        self._brightness = 100
        self._state = False
        self._last_known_state = None
        self._is_online = True
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("light", self.update_state)
        self.command = LightCommand(host,module_address,loop_address,gradient_time)
        if self._sub_device_type == "rgb":
            self._color_temp_mireds = 370
            self._min_mireds = 152
            self._max_mireds = 667
            self._color_temp_kelvin = int(1000000 / 370)  # converting mireds to kelvin
            self._attr_min_color_temp_kelvin = int(1000000 / 667)  # converting max mireds to kelvin
            self._attr_max_color_temp_kelvin = int(1000000 / 152)  # converting min mireds to kelvin
            self._color_mode = ColorMode.RGB
            self._rgb_color = (255, 255, 255)
            self._supported_features = SUPPORT_COLOR
            self._supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.RGB }
        elif self._sub_device_type in ("DALI-01", "DALI-02"):
            self._color_temp_mireds = 370
            self._min_mireds = 152
            self._max_mireds = 667
            self._color_temp_kelvin = int(1000000 / 370)  # converting mireds to kelvin
            self._attr_min_color_temp_kelvin = int(1000000 / 667)  # converting max mireds to kelvin
            self._attr_max_color_temp_kelvin = int(1000000 / 152)  # converting min mireds to kelvin
            self._supported_color_modes = {ColorMode.COLOR_TEMP}
        elif self._sub_device_type in ("single", "0603D"):
            self._supported_color_modes = {ColorMode.BRIGHTNESS}

    async def async_added_to_hass(self):
        """Callback when entity is added to hass."""
        self.hass.async_create_task(self.async_update())
        self.async_write_ha_state()

    @property
    def unique_id(self):
        """Return a unique ID for this light."""
        return f"{self._module_address}_{self._loop_address}_light"

    @property
    def is_on(self):
        return self._state

    @property
    def brightness(self):
        return self._brightness

    @property
    def rgb_color(self):
        return self._rgb_color

    @property
    def color_mode(self):
        return self._color_mode

    @property
    def color_temp(self):
        return self._color_temp_mireds

    @property
    def color_temp_kelvin(self):
        return int(1000000 / self._color_temp_mireds)

    @property
    def min_mireds(self):
        return self._min_mireds

    @property
    def max_mireds(self):
        return self._max_mireds

    @property
    def supported_color_modes(self):
        return self._supported_color_modes

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_light")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Light Model",
        }

    @property
    def available(self):
        """Return True if the device is available (online)."""
        self._is_online = True
        return self._is_online

    async def async_turn_on(self, **kwargs):
        self._state = True
        command_list = []
        # command_list.append(self.command.turnonoff("on"))

        if "brightness" in kwargs:
            brightness_value = kwargs["brightness"]
            self._brightness = brightness_value
            self._brightness_percentage = int((brightness_value / 255) * 100)
            match self._sub_device_type:
                case "0603D":
                    hex_command = self.command.brightness(self._brightness_percentage)
                case "rgb":
                    hex_command = self.command.brightness(self._brightness_percentage)
                case "DALI-01":
                    hex_command = self.command.dali01_brightness(self._brightness_percentage)
                case "DALI-02":
                    hex_command = self.command.dali02_brightness(self._brightness_percentage)
                case "single":
                    hex_command = self.command.brightness(self._brightness_percentage)
            command_list.append(hex_command)
        if "color_temp_kelvin" in kwargs:
            self._color_temp_kelvin = kwargs["color_temp_kelvin"]
            self._color_temp_mireds = int(1000000 / self._color_temp_kelvin)
            kelvin_value = str(kwargs['color_temp_kelvin'])[:2]
            match self._sub_device_type:
                case "rgb":
                    hex_command = self.command.rgb_color_temp(kelvin_value)
                case "DALI-01":
                    hex_command = self.command.dali01_color_temp(kelvin_value)
                case "DALI-02":
                    hex_command = self.command.dali02_color_temp(kelvin_value)
            command_list.append(hex_command)
        if "rgb_color" in kwargs:
            self._rgb_color = kwargs["rgb_color"]
            r, g, b = kwargs["rgb_color"]
            hex_command = self.command.rgb_color(r, g, b)
            command_list.append(hex_command)

        self.async_write_ha_state()
        await self.tcp_manager.send_command_list(command_list)


    async def async_turn_off(self, **kwargs):
        self._state = False
        self.async_write_ha_state()
        await self.tcp_manager.send_command(self.command.turnonoff("off"))


    async def async_update(self):
        # self._state = True
        # self.async_write_ha_state()
        return

    def update_state(self, response_dict):
        print('DALI收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']

        if response_dict['sub_device_type'] == 'DALI-01' and response_dict['data4'] == 0x11:
            device._brightness = response_dict['data1'] * 255 / 100
            if response_dict['data1'] == 0x00:
                device._state = False
            else:
                device._state = True

        elif response_dict['sub_device_type'] == 'DALI-01' and response_dict['data4'] == 0x12:
            if response_dict['data1'] != 0x00:
                device._color_temp_mireds = 1000000/(response_dict['data1']*100)
                device._color_temp_kelvin = int(1000000 / device._color_temp_mireds)

        elif response_dict['sub_device_type'] == 'rgb' and response_dict['data4'] == 0x13:
            if response_dict['data1'] != 0x00:
                device._rgb_color = (
                response_dict['data1'],  # R 值
                response_dict['data2'],  # G 值
                response_dict['data3']   # B 值
                )
                device._state = True
                device.async_write_ha_state()
        elif response_dict['sub_device_type'] == 'DALI-02' and response_dict['data4'] == 0x15:
            device._brightness = response_dict['data1'] * 255 / 100
            if response_dict['data1'] == 0x00:
                device._state = False
            else:
                device._state = True
            if response_dict['data2'] != 0x00:
                device._color_temp_mireds = 1000000/(response_dict['data2']*100)
                device._color_temp_kelvin = int(1000000 / device._color_temp_mireds)

        elif response_dict['sub_device_type'] == '0603D' and response_dict['data4'] == 0x10:
            device._brightness = response_dict['data1'] * 255 / 100
            if response_dict['data1'] == 0x00:
                device._state = False
            else:
                device._state = True
        device.async_write_ha_state()
