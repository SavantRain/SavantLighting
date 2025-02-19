from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_platform import async_get_platforms
from homeassistant.const import Platform
from .tcp_manager import TCPConnectionManager


PLATFORMS = [Platform.LIGHT, Platform.SWITCH, Platform.CLIMATE, Platform.FAN, Platform.COVER, Platform.BINARY_SENSOR]
tcp_manager = None

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Savant Lighting component."""
    # hass.states.async_set(f"{DOMAIN}.status", "initialized")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Savant Lighting from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # 保存配置信息
    tcp_manager = TCPConnectionManager(entry.data.get("host"), entry.data.get("port"), None)
    tcp_manager.set_hass(hass)
    await tcp_manager.connect()
    
    hass.data[DOMAIN][entry.entry_id] = {
        "host": entry.data.get("host"),
        "port": entry.data.get("port"),
        "tcp_manager": tcp_manager,
        "devices": entry.data.get("devices", []), 
    }
        
    @callback
    def handle_ha_started(event):
        devices = hass.data[DOMAIN][entry.entry_id].get("devices")
        hass.async_create_task(tcp_manager.update_all_device_state(devices))
    
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, handle_ha_started)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_update_config_entry(hass: HomeAssistant, entry_id: str, new_data: dict) -> None:
    """Update the config entry data in the Home Assistant database."""
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry:
        # 合并新数据和现有数据
        updated_data = {**entry.data, **new_data}
        hass.config_entries.async_update_entry(entry, data=updated_data)
        
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up the integration data
        hass.data[DOMAIN].pop(entry.entry_id)

        # Clean up the device registry data
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        # 删除与该配置条目关联的设备和实体
        device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
        for device_entry in device_entries:
            device_registry.async_remove_device(device_entry.id)

        entity_entries = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        for entity_entry in entity_entries:
            entity_registry.async_remove(entity_entry.entity_id)

    return unload_ok