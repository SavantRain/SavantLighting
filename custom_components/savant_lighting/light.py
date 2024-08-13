import logging
from homeassistant.components.light import LightEntity
from homeassistant.const import STATE_ON, STATE_OFF

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """配置灯光实体。"""
    # 创建并添加灯光实体
    async_add_entities([ExampleLight()])


class ExampleLight(LightEntity):
    """示例灯光实体类。"""

    def __init__(self):
        """初始化灯光实体。"""
        self._state = STATE_OFF
        self._name = "Example Light"

    @property
    def name(self):
        """返回灯光名称。"""
        return self._name

    @property
    def is_on(self):
        """返回灯光状态。"""
        return self._state == STATE_ON

    def turn_on(self, **kwargs):
        """打开灯光。"""
        _LOGGER.info("Turning on the light")
        self._state = STATE_ON
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """关闭灯光。"""
        _LOGGER.info("Turning off the light")
        self._state = STATE_OFF
        self.schedule_update_ha_state()

    def toggle(self, **kwargs):
        """切换灯光状态。"""
        if self._state == STATE_ON:
            self.turn_off()
        else:
            self.turn_on()