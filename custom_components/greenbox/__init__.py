"""GreenBox (BerlinGreen indoor garden) over Bluetooth LE."""

from __future__ import annotations

from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .coordinator import GreenBoxConfigEntry, GreenBoxCoordinator

PLATFORMS = [Platform.LIGHT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: GreenBoxConfigEntry) -> bool:
    coordinator = GreenBoxCoordinator(hass, entry, entry.data[CONF_ADDRESS])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GreenBoxConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
