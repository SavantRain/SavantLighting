from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import async_add_entities
from homeassistant.const import Platform
from .const import DOMAIN
from .light import SavantLight
from .switch import SavantSwitch

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Gateway from a config entry."""
    # 获取网关配置（host 和 port）
    host = entry.data["host"]
    port = entry.data["port"]
    
    # 创建网关实体
    gateway = SavantGateway(name=f"Savant Gateway ({host}:{port})", host=host, port=port)
    async_add_entities([gateway])

    # 根据配置创建设备实体（灯光和开关）
    devices = entry.data.get("devices", [])
    device_entities = []

    for device in devices:
        if device["type"] == "light":
            device_entities.append(
                SavantLight(device["name"], device["module_address"], device["loop_address"], gateway)
            )
        elif device["type"] == "switch":
            device_entities.append(
                SavantSwitch(device["name"], device["module_address"], device["loop_address"], gateway)
            )

    # 添加设备到 Home Assistant
    async_add_entities(device_entities)

class SavantGateway(Entity):
    """Representation of a Savant Gateway."""

    def __init__(self, name, host, port):
        """Initialize the Savant Gateway."""
        self._attr_name = name
        self._host = host
        self._port = port
        self._attr_unique_id = f"{host}:{port}_gateway"
        self._is_connected = False

    @property
    def unique_id(self):
        """Return a unique ID for the gateway."""
        return self._attr_unique_id

    @property
    def is_on(self):
        """Return True if the gateway is connected."""
        return self._is_connected

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the gateway."""
        return {
            "host": self._host,
            "port": self._port,
        }

    async def async_added_to_hass(self):
        """Handle when the gateway entity is added to Home Assistant."""
        await self.async_connect_to_gateway()

    async def async_will_remove_from_hass(self):
        """Handle when the gateway entity is removed from Home Assistant."""
        await self.async_disconnect_from_gateway()

    async def async_connect_to_gateway(self):
        """Connect to the gateway."""
        # 实现与网关的连接逻辑
        self._is_connected = True  # 模拟连接成功
        self.async_write_ha_state()

    async def async_disconnect_from_gateway(self):
        """Disconnect from the gateway."""
        # 实现与网关的断开连接逻辑
        self._is_connected = False
        self.async_write_ha_state()
