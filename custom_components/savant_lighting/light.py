from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Light entities from a config entry."""
    config = hass.data[DOMAIN].get(entry.entry_id, {}).get("devices", [])
    
    # 创建所有已配置的灯光实体并添加到 Home Assistant
    lights = [
        SavantLight(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
        )
        for device in config if device["type"] == "light"
    ]
    async_add_entities(lights, update_before_add=True)

class SavantLight(LightEntity):
    """Representation of a Savant Light."""

    def __init__(self, name, module_address, loop_address, host, port):
        """Initialize the Savant Light."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._attr_unique_id = f"{module_address}_{loop_address}_light"
        self._attr_supported_color_modes = {ColorMode.HS, ColorMode.BRIGHTNESS}  # 支持HS颜色模式和亮度
        self._attr_color_mode = ColorMode.HS
        self._state = False
        self._brightness = 255
        self._hs_color = (0, 0)
    
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
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}")}
        }

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        self._state = True
        if "brightness" in kwargs:
            self._brightness = kwargs["brightness"]
        if "hs_color" in kwargs:
            self._hs_color = kwargs["hs_color"]
            self._attr_color_mode = ColorMode.HS

        # 将状态发送到实际设备
        await self._send_state_to_device()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        self._state = False

        # 将状态发送到实际设备
        await self._send_state_to_device()
        self.async_write_ha_state()

    async def _send_state_to_device(self):
        """Send the current state to the actual device."""
        # 在这里实现与实际硬件设备通信的逻辑
        # 这可以是通过 REST API 调用、MQTT 消息或其他协议
        host = self._host
        port = self._port
        module_address = self._module_address
        loop_address = self._loop_address
        print(f"{host}:{port} {module_address}:{loop_address}")
        pass

    async def async_update(self):
        """Fetch new state data for this light."""
        # 从实际设备获取新的状态数据
        # 例如，调用 REST API 端点或读取 MQTT 主题
        self._state = True  # 更新为实际状态
        self._brightness = 255  # 更新为实际亮度
        self._hs_color = (0, 0)  # 更新为实际颜色