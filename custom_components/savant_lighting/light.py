import logging
from datetime import timedelta
from homeassistant.components.light import LightEntity, ColorMode
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

    def __init__(self, name, module_address, loop_address, host, port, sub_device_type, tcp_manager):
        """Initialize the Savant Light."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._sub_device_type = sub_device_type
        self._brightness = 100
        self._state = False
        self._last_known_state = None
        self._is_online = True
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("light", self.update_state)
        self.command = LightCommand(host,module_address,loop_address)
        if self._sub_device_type == "rgb":
            self._color_temp = 370
            self._min_mireds = 152
            self._max_mireds = 667
            self._color_mode = ColorMode.HS
            self._hs_color = (0, 0)
            self._supported_color_modes = {ColorMode.HS, ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}  # 支持HS颜色模式和亮度
        elif self._sub_device_type == "0603D":
            self._supported_color_modes = {ColorMode.BRIGHTNESS}
        elif self._sub_device_type == "DALI-01":
            self._color_temp = 370
            self._min_mireds = 152
            self._max_mireds = 667
            self._supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}  # 支持HS颜色模式和亮度
        elif self._sub_device_type == "DALI-02":
            self._color_temp = 370
            self._min_mireds = 152
            self._max_mireds = 667
            self._supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}  # 支持HS颜色模式和亮度
        else:
            self._supported_color_modes = {ColorMode.BRIGHTNESS}  # 支持HS颜色模式和亮

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
        """Return true if the light is on."""
        return self._state

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def hs_color(self):
        """Return the hue and saturation color value."""
        return self._hs_color
    
    @property
    def color_temp(self):
        """Return the color temperature."""
        return self._color_temp

    @property
    def min_mireds(self):
        return self._min_mireds
    
    @property
    def max_mireds(self):
        return self._max_mireds

    @property
    def supported_color_modes(self):
        """Flag supported color modes."""
        return self._supported_color_modes

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}")},
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
        if "brightness" in kwargs:
            brightness_value = kwargs["brightness"]
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
                case "":
                    hex_command = self.command.brightness(self._brightness_percentage)
                case None:
                    hex_command = self.command.brightness(self._brightness_percentage)
            await self.tcp_manager.send_command(hex_command)
        if "color_temp_kelvin" in kwargs:
            self.color_temp_kelvin_value = str(kwargs['color_temp_kelvin'])[:2]
            self._color_mode = ColorMode.COLOR_TEMP
            match self._sub_device_type:
                case "rgb": 
                    hex_command = self.command.rgb_color_temp(self.color_temp_kelvin_value)
                case "DALI-01": 
                    hex_command = self.command.dali01_color_temp(self.color_temp_kelvin_value)
                case "DALI-02":
                    hex_command = self.command.dali02_color_temp(self.color_temp_kelvin_value)
            await self.tcp_manager.send_command(hex_command)
        if "hs_color" in kwargs:
            self._hs_color = kwargs["hs_color"]
            self._color_mode = ColorMode.HS
            hex_command = self.command.rgb_color(self._hs_color)
            await self.tcp_manager.send_command(hex_command)
        
        hex_command = self.command.turnonoff("on")
        await self.tcp_manager.send_command(hex_command)

    async def async_turn_off(self, **kwargs):
        self._state = True
        await self.tcp_manager.send_command(self.command.turnonoff("off"))

    def _register_callback(self):
        """返回处理自己的状态更新回调"""
        def callback(response, device_type):
            if device_type in self.device_type:
                self.update_state(response)
        return callback

    async def async_update(self):
        self._state = True
        # await self.tcp_manager.send_command(self.command.query_state())

    def update_state(self, response_dict):
        print('开关收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']

        if response_dict['sub_device_type'] == 'DALI-01':
            if response_dict['data4'] == 0x11:
                device._brightness = response_dict['data1'] * 255 / 100
                if response_dict['data1'] == 0x00:
                    device._state = False
                else:
                    device._state = True
            if response_dict['data4'] == 0x12:

                device._color_temp = 1000000/(response_dict['data1']*100)

        # device._state = self._parse_device_state(response_dict['response_str'])
        device.async_write_ha_state()

    # def _parse_device_state(device, response):
    #     try:
    #         #亮度回复   AC E6 00 11 02 01 00 04 64 00 00 11（DALI01亮度标识符） CA
    #         #色温回复   AC E6 00 11 02 02 00 04 41 00 00 12（DALI01色温标识符） CA
    #         if len(response) >= 12:
    #             device_value = response[8]       #数据    
    #             device_type = response[11]  #类型    0X11为DALI01亮度     0X12为DALI01色温

    #             if device_type == 'DALI-01':
    #                 if device_type == 0x12:
    #                     device_value = 45
    #                     device._color_temp = 1000000/(device_value*100)
    #                 elif device_type == 0x11:
    #                     device._brightness = device_value * 255 / 100
    #             return True
    #         else:
    #             _LOGGER.error("无效的设备回复长度：{len(response)}")
    #             return None
    #     except Exception as e:
    #         _LOGGER.error("解析设备状态出错：{e}")
    #         return None