"""Separate weekend schedule on/off (the box treats weekend duration 0 as off)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GreenBoxConfigEntry
from .entity import GreenBoxEntity
from .protocol import MIN_HOURS, REG_WEEKDAY_HOURS, REG_WEEKEND_HOURS


async def async_setup_entry(
    hass: HomeAssistant, entry: GreenBoxConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GreenBoxWeekendSchedule(entry.runtime_data, "weekend_schedule")])


class GreenBoxWeekendSchedule(GreenBoxEntity, SwitchEntity):
    _attr_translation_key = "weekend_schedule"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data[REG_WEEKEND_HOURS] > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        hours = max(MIN_HOURS, self.coordinator.data[REG_WEEKDAY_HOURS])
        await self.coordinator.async_write({REG_WEEKEND_HOURS: hours})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write({REG_WEEKEND_HOURS: 0})
