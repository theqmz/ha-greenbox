"""Light-on time of the box's own schedule, for weekdays and weekends.

The box stores the time as HHMM in UTC; we show and accept local time.
"""

from __future__ import annotations

from datetime import UTC, time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import GreenBoxConfigEntry
from .entity import GreenBoxEntity
from .protocol import REG_WEEKDAY_START, REG_WEEKEND_START


def utc_hhmm_to_local(value: int) -> time:
    utc = dt_util.utcnow().replace(hour=value // 100 % 24, minute=value % 100, second=0, microsecond=0)
    return dt_util.as_local(utc).time().replace(tzinfo=None)


def local_to_utc_hhmm(value: time) -> int:
    local = dt_util.now().replace(hour=value.hour, minute=value.minute, second=0, microsecond=0)
    utc = local.astimezone(UTC)
    return utc.hour * 100 + utc.minute


async def async_setup_entry(
    hass: HomeAssistant, entry: GreenBoxConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            GreenBoxStartTime(coordinator, "weekday_start", REG_WEEKDAY_START),
            GreenBoxStartTime(coordinator, "weekend_start", REG_WEEKEND_START),
        ]
    )


class GreenBoxStartTime(GreenBoxEntity, TimeEntity):
    def __init__(self, coordinator, key: str, register: str) -> None:
        super().__init__(coordinator, key)
        self._attr_translation_key = key
        self._register = register

    @property
    def native_value(self) -> time:
        return utc_hhmm_to_local(self.coordinator.data[self._register])

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_write({self._register: local_to_utc_hhmm(value)})
