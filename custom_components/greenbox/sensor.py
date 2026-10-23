"""Raw values of registers we have not decoded yet (diagnostic, to find water level etc.)."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GreenBoxConfigEntry
from .entity import GreenBoxEntity
from .protocol import UNKNOWN_REGISTERS


async def async_setup_entry(
    hass: HomeAssistant, entry: GreenBoxConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(GreenBoxRawSensor(coordinator, reg) for reg in UNKNOWN_REGISTERS)


class GreenBoxRawSensor(GreenBoxEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, register: str) -> None:
        # Lower- and upper-case registers differ ("S" vs "s"), so keep both apart in the id.
        key = f"reg_{register}" if register.isupper() else f"reg_{register}_lc"
        super().__init__(coordinator, key)
        self._register = register
        self._attr_name = f"Register {register}"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get(self._register)
