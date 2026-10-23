"""Light duration of the box's own schedule, for weekdays and weekends."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GreenBoxConfigEntry
from .entity import GreenBoxEntity
from .protocol import MAX_HOURS, MIN_HOURS, REG_WEEKDAY_HOURS, REG_WEEKEND_HOURS


async def async_setup_entry(
    hass: HomeAssistant, entry: GreenBoxConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            GreenBoxDuration(coordinator, "weekday_hours", REG_WEEKDAY_HOURS),
            GreenBoxDuration(coordinator, "weekend_hours", REG_WEEKEND_HOURS),
        ]
    )


class GreenBoxDuration(GreenBoxEntity, NumberEntity):
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_native_min_value = MIN_HOURS
    _attr_native_max_value = MAX_HOURS
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, key: str, register: str) -> None:
        super().__init__(coordinator, key)
        self._attr_translation_key = key
        self._register = register

    @property
    def native_value(self) -> int | None:
        # 0 on the weekend means "no separate weekend schedule", shown as unknown here.
        return self.coordinator.data[self._register] or None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write({self._register: int(value)})
