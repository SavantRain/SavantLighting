from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_platform import async_get_platforms

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Savant Lighting component."""
    # hass.states.async_set(f"{DOMAIN}.status", "initialized")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Savant Lighting from a config entry."""
    config = entry.data
    device_type = config["type"]
    name = config["name"]
    host = config["host"]
    port = config["port"]

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
        
    # Create or update device
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, f"{host}:{port}")},
        identifiers={(DOMAIN, f"{host}:{port}_{name}")},
        manufacturer="Savant",
        name=name,
        model=device_type.capitalize(),
        sw_version="1.0",
    )
    
    # Forward the setup to the correct platform (light or switch)
    platforms = []
    if device_type == "light":
        platforms.append("light")
    elif device_type == "switch":
        platforms.append("switch")

    # Pass the device_id to the platform setup
    hass.data[DOMAIN][entry.entry_id] = {
        "device_id": device.id,
        "host": host,
        "port": port,
        "name": name
    }

    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    return True


# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
#     """Unload a config entry."""
#     # Unload the platforms
#     unload_ok = await hass.config_entries.async_unload_platforms(entry, ["light", "switch"])

#     # Clean up the registry data if needed
#     if unload_ok:
#         device_registry = dr.async_get(hass)
#         entity_registry = er.async_get(hass)
        
#         device_registry.async_clear_config_entry(entry.entry_id)
#         entity_registry.async_clear_config_entry(entry.entry_id)
        
#         hass.data[DOMAIN].pop(entry.entry_id, None)

#     return unload_ok