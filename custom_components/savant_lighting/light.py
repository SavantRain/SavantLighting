"""Platform for Savant Lighting light integration."""
import logging
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    LightEntity,
)
from homeassistant.const import STATE_ON, STATE_OFF
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Savant Lighting lights from a config entry."""
    config = config_entry.data
    name = config["name"]
    host = config["host"]
    port = config["port"]
    
    # 创建一个自定义的灯实体并添加到 Home Assistant
    entity = SavantLight(name, host, port)
    async_add_entities([entity], update_before_add=True)

class SavantLight(LightEntity):
    """Representation of a Savant Light."""

    def __init__(self, name, host, port):
        """Initialize the light."""
        self._name = name
        self._host = host
        self._port = port
        self._state = STATE_OFF
        self._brightness = 255
        self._hs_color = (0, 0)

    @property
    def unique_id(self):
        """Return a unique ID for this light."""
        return f"{self._host}_{self._port}_{self._name}_light"

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state == STATE_ON

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def hs_color(self):
        """Return the color of the light."""
        return self._hs_color

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        self._state = STATE_ON
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
        if ATTR_HS_COLOR in kwargs:
            self._hs_color = kwargs[ATTR_HS_COLOR]

        # 将状态发送给实际的硬件设备
        await self._send_state_to_device()

        # 通知 Home Assistant 更新实体状态
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        self._state = STATE_OFF

        # 将状态发送给实际的硬件设备
        await self._send_state_to_device()

        # 通知 Home Assistant 更新实体状态
        self.async_write_ha_state()

    async def _send_state_to_device(self):
        """Send the state to the device."""
        _LOGGER.debug(
            f"Sending state to device: state={self._state}, brightness={self._brightness}, color={self._hs_color}"
        )
        # 示例：假设你有一个函数 send_command_to_device(host, port, command)
        # command = self._create_command()
        # await send_command_to_device(self._host, self._port, command)

    async def async_update(self):
        """Fetch new state data for this light."""
        # 这里添加从实际设备获取状态的逻辑
        # 例如：await self._fetch_state_from_device()

        if not self.entity_id:
            return

        self._state = STATE_ON
        self._brightness = 255
        self._hs_color = (0, 0)

        # 通知 Home Assistant 更新实体状态
        self.async_write_ha_state()
