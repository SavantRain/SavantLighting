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
from .switch_with_energy import SavantEnergySwitch

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
            scene_number=device["scene_number"],
            host=device["host"],
            port=device["port"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "scene_switch"
    ]

    energy_switches = [
        SavantEnergySwitch(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
            tcp_manager=config["tcp_manager"]
        )
        for device in devices if device["type"] == "switch_with_energy"
    ]

    async_add_entities(switchs + eight_buttons + scene_switchs + energy_switches, update_before_add=True)

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
        # query_command = self._generate_query_command()
        # await self.tcp_manager.send_command(query_command)


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
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}_switch")},
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

    def _generate_query_command(self) -> bytes:
        """Generate the query command to get the device state."""
        host_hex = f"AC{int(self._host.split('.')[-1]):02X}00B0"
        module_hex = f"{int(self._module_address):02X}"
        base_command = bytes.fromhex(host_hex + module_hex)
        return base_command + b'\x01\x00\x01\x08\xCA'

    def update_state(self, response_dict):
        print('继电器收到状态响应: ' + str(response_dict).replace('\\x', ''))
        device = response_dict['device']
        if response_dict["switch_type"] == "num0":
            if response_dict["data1"] == 0x00:
                device._state = False
            else:
                device._state = True

        device.async_write_ha_state()