import logging
from datetime import timedelta
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .send_command import send_tcp_command

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Light entities from a config entry."""
    config = hass.data[DOMAIN].get(entry.entry_id, {}).get("devices", [])
    
    lights = [
        SavantLight(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
            sub_device_type=device["sub_device_type"]
        )
        for device in config if device["type"] == "light"
    ]
    async_add_entities(lights, update_before_add=True)

class SavantLight(LightEntity):
    """Representation of a Savant Light."""

    def __init__(self, name, module_address, loop_address, host, port, sub_device_type):
        """Initialize the Savant Light."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._sub_device_type = sub_device_type
        self._brightness = 100
        self._state = False
        self._last_known_state = None  # 用于存储最后已知状态
        self._is_online = True  # 在线状态初始化为
        if self._sub_device_type == "rgb":
            self._color_temp = 370
            self._min_mireds = 152
            self._max_mireds = 667
            self._color_mode = ColorMode.HS
            self._hs_color = (0, 0)
            self._supported_color_modes = {ColorMode.HS, ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}  # 支持HS颜色模式和亮度
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
        _LOGGER.debug(f"{self.name} has been added to hass")
        # 延迟更新设备状态，以避免阻塞 setup
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
        """Turn on the light."""
        self._state = True
        if "brightness" in kwargs:
            brightness_value = kwargs["brightness"]
            self._brightness_percentage = int((brightness_value / 255) * 100)
            await self._send_state_to_device("brightness")
        if "color_temp_kelvin" in kwargs:
            self.color_temp_kelvin_value = str(kwargs['color_temp_kelvin'])[:2]
            self._color_mode = ColorMode.COLOR_TEMP
            await self._send_state_to_device("color_temp")
        if "hs_color" in kwargs:
            self._hs_color = kwargs["hs_color"]
            self._color_mode = ColorMode.HS
            await self._send_state_to_device("hs_color")
        await self._send_state_to_device("on")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        self._state = False
        await self._send_state_to_device("off")
        self.async_write_ha_state()

    async def async_update(self):
        try:
            response = await self._get_state_from_device()
            if response is not None:
                self._state = self._parse_device_state(response)
                self._is_online = True
                self._brightness = 255  # 更新为实际亮度
                self._hs_color = (0, 0)  # 更新为实际颜色
            else:
                self._is_online = False
        except Exception:
            self._is_online = False  # 如果获取状态失败，则设备离线
            
    async def _send_state_to_device(self, command):
        hex_command = self._command_to_hex(command)
        response, is_online = await send_tcp_command(self._host, self._port, hex_command)
        
    async def _get_state_from_device(self):
        hex_command = self._query_to_hex("get_state")
        response, is_online = await send_tcp_command(self._host, self._port, hex_command)
        return response

    # def _query_to_hex(self, command):
    #     #查询指令
    #     host_hex = f"AC{int(self._host.split('.')[-1]):02X}"
    #     module_hex = f"{int(self._module_address):02X}00B0"
    #     command_hex = '01000108CA'
    #     host_bytes = bytes.fromhex(host_hex)
    #     module_bytes = bytes.fromhex(module_hex)
    #     command_bytes = bytes.fromhex(command_hex)
    #     command = host_bytes + module_bytes + command_bytes
    #     return command

    def _command_to_hex(self, command):
        """将'开'和'关'的命令转换为十六进制格式"""
        #指令第二个字节为IP的最后一位，如192.168.1.230，将230转化为十六进制E6在指令中进行传输
        host_hex = f"AC{int(self._host.split('.')[-1]):02X}0010"
        module_hex = f"{int(self._module_address):02X}"
        loop_hex = f"{int(self._loop_address):02X}"
        # 处理RGB灯光的开关操作
        if self._sub_device_type == "rgb":
            if command == "on":
                command_hex = '000401000000CA'
            elif command == "off":
                command_hex = '000400000000CA'
            else:
                command_hex = ''
        # 处理双色温灯光的开关操作
        elif self._sub_device_type == "DALI-01":
            if command == "on":
                command_hex = f'{loop_hex}000401000001CA'   #状态开启
            elif command == "off":
                command_hex = f'{loop_hex}000400000001CA'   #状态关闭
            elif command == "brightness":
                brightness_hex = f"{int(self._brightness_percentage):02X}" if self._brightness_percentage is not None else '00'
                command_hex = f'{loop_hex}0004{brightness_hex}000010CA'
                #亮度回复   AC E6 00 11 02 01 00 04 64 00 00 11（DALI01亮度标识符） CA
            elif command == "color_temp":
                # 将十六进制字符串转换回整数，加1后再转换回十六进制字符串并赋值给loop_hex_value
                loop_hex_value = int(loop_hex, 16)
                loop_hex_value += 1
                loop_hex_original = f"{loop_hex_value:02X}"
                color_temp_hex = f"{int(self.color_temp_kelvin_value):02X}" if self.color_temp_kelvin_value is not None else '00'
                command_hex = f'{loop_hex_original}0004{color_temp_hex}000000CA'
                #色温回复   AC E6 00 11 02 02 00 04 41 00 00 12（DALI01色温标识符） CA
            else:
                command_hex = ''
        elif self._sub_device_type == "DALI-02":
            if command == "on":
                command_hex = f'{loop_hex}000401000001CA'   #状态开启
            elif command == "off":
                command_hex = f'{loop_hex}000400000001CA'   #状态关闭
            elif command == "brightness":
                brightness_hex = f"{int(self._brightness_percentage):02X}" if self._brightness_percentage is not None else '00'
                command_hex = f'{loop_hex}0004{brightness_hex}00FF10CA'
            elif command == "color_temp":
                color_temp_hex = f"{int(self.color_temp_kelvin_value):02X}" if self.color_temp_kelvin_value is not None else '00'
                command_hex = f'{loop_hex}0004FF00{color_temp_hex}10CA'
            else:
                command_hex = ''
        # 处理单色温灯光的开关操作
        else:
            if command == "on":
                command_hex = f'{loop_hex}000401000001CA'   #状态开启
            elif command == "off":
                command_hex = f'{loop_hex}000400000001CA'   #状态关闭
            elif command == "brightness":
                brightness_hex = f"{int(self._brightness_percentage):02X}" if self._brightness_percentage is not None else '00'
                command_hex = f'{loop_hex}0004{brightness_hex}000010CA'
            else:
                command_hex = ''
        host_bytes = bytes.fromhex(host_hex)
        module_bytes = bytes.fromhex(module_hex)
        command_bytes = bytes.fromhex(command_hex)
        command = host_bytes + module_bytes + command_bytes
        print(command)
        return command

    def _parse_device_state(self, response):
        try:
            #亮度回复   AC E6 00 11 02 01 00 04 64 00 00 11（DALI01亮度标识符） CA
            #色温回复   AC E6 00 11 02 02 00 04 41 00 00 12（DALI01色温标识符） CA
            print(response)
            if len(response) >= 12:
                loop_hex = f"{int(self._loop_address):02X}"
                modubleID =response[5]      #通道地址
                device_value = response[9]       #数据    
                device_type = response[11]  #类型    0X11为DALI01亮度     0X12为DALI01色温

                if device_type == 'DALI01':
                    if device_type == 12:
                        device_value = 45
                        self._color_temp = 1000000/(device_value*100)
                    elif device_type == 11:
                        self._brightness = device_value * 255 / 100
                return True
            else:
                _LOGGER.error("无效的设备回复长度：{len(response)}")
                return None
        except Exception as e:
            _LOGGER.error("解析设备状态出错：{e}")
            return None