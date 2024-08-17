from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from homeassistant.helpers import device_registry as dr, entity_registry as er

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Savant Lighting component."""
    hass.states.async_set(f"{DOMAIN}.status", "initialized")
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

    # Create or update device
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, f"{host}:{port}")},
        identifiers={(DOMAIN, f"{host}:{port}")},
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

    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    return True
