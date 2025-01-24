import logging
from datetime import timedelta
from homeassistant.components.switch import SwitchEntity
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
    switchs = [
        SavantSwitch(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "switch"
    ]
    
    eight_buttons = []
    for device in devices:
        if device["type"] == "8button":  # 检查设备类型是否为 8 键开关
            for button_index in device['selected_buttons']:  # 为每个按键创建一个实体
                eight_buttons.append(
                    SavantSwitch8Button(
                        name=f"{device['name']}",
                        module_address=device["module_address"],
                        loop_address=device["loop_address"],
                        button_index=button_index,
                        host=device["host"],
                        port=device["port"],
                        tcp_manager=config["tcp_manager"],
                    )
                )

    scene_switchs = [
        SavantSwitchScene(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "scene_switch"
    ]
    
    async_add_entities(switchs + eight_buttons + scene_switchs, update_before_add=True)

class SavantSwitch(SwitchEntity):
    """Representation of a Savant Switch."""

    def __init__(self, name, module_address, loop_address, host, port, tcp_manager):
        """Initialize the switch."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._state = False
        self._last_known_state = None  # 用于存储最后已知状态
        self._is_online = True  # 在线状态初始化为
        self.tcp_manager = tcp_manager
        self.tcp_manager.register_callback("switch", self.update_state)
        self.command = SwitchCommand(host,module_address,loop_address)
        
    async def async_added_to_hass(self):
        """Callback when entity is added to hass."""
        # 延迟更新设备状态，以避免阻塞 setup
        self.hass.async_create_task(self.async_update())
        self.async_write_ha_state()
        
    @property
    def unique_id(self):
        """Return a unique ID for this light."""
        return f"{self._module_address}_{self._loop_address}_switch"
    
    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}")},
            "name": self._attr_name,
            "manufacturer": "Savant",
            "model": "Switch Model",
        }
    
    @property
    def available(self):
        """Return True if the device is available (online)."""
        self._is_online = True
        return self._is_online

    async def async_turn_on(self, **kwargs):
        self._state = True
        await self.tcp_manager.send_command(self.command.turnonoff("on"))

    async def async_turn_off(self, **kwargs):
        self._state = True
        await self.tcp_manager.send_command(self.command.turnonoff("off"))
    
    async def async_update(self):
        self._state = True
        # await self.tcp_manager.send_command(self.command.query_state())
        # 此代码如果不注释，会在每次执行操作后，进行状态查询。

    def update_state(self, response_dict):
        print('开关收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']
        device._state = self._parse_device_state(response_dict['response_str'])
        device.async_write_ha_state()
        
    def _parse_device_state(self, response):
        try:
            if len(response) >= 12:
                relay_state = response[8]

                if relay_state == 0x01:
                    return True
                elif relay_state == 0x00:
                    return False
                else:
                    _LOGGER.warning("无法解析继电器状态：{relay_state}")
                    #转
            else:
                _LOGGER.error("无效的设备回复长度：{len(response)}")
        except Exception as e:
            _LOGGER.error("解析设备状态出错：{e}")
            return True
