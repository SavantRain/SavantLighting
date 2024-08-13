"""Support for SavantLighting."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# 定义日志记录器
_LOGGER = logging.getLogger(__name__)

# 定义域名（需与 manifest.json 中的 domain 一致）
DOMAIN = "savant.com.cn"

# 在 Home Assistant 启动时调用
async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """配置集成所需的基本设置。"""
    _LOGGER.info("Setting up the integration")
    
    # 示例：注册一个服务
    async def handle_service(call):
        """处理服务调用的逻辑。"""
        _LOGGER.info("Service called with data: %s", call.data)
    
    hass.services.async_register(DOMAIN, "example_service", handle_service)
    
    return True

# 在通过配置界面设置集成时调用
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """从配置条目设置集成。"""
    _LOGGER.info("Setting up the integration from config entry")
    
    # 你可以在这里初始化你的平台，例如传感器、开关等
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "light")
    )
    return True

# 在配置条目更新时调用
async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """更新配置条目时调用。"""
    _LOGGER.info("Updating the integration with new config entry")
    
    # 更新逻辑可以放在这里

# 在配置条目卸载时调用
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目时调用。"""
    _LOGGER.info("Unloading the integration")
    
    # 卸载平台，例如传感器、开关等
    await hass.config_entries.async_forward_entry_unload(entry, "light")
    
    return True