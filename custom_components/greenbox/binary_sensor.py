"""Water sensor in the tank: only reports wet or dry, not a level."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GreenBoxConfigEntry
from .entity import GreenBoxEntity
from .protocol import REG_WATER


async def async_setup_entry(
    hass: HomeAssistant, entry: GreenBoxConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GreenBoxWaterEmpty(entry.runtime_data, "water_empty")])


class GreenBoxWaterEmpty(GreenBoxEntity, BinarySensorEntity):
    _attr_translation_key = "water_empty"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool:
        return self.coordinator.data[REG_WATER] == 0
