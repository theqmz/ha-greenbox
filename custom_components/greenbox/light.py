"""GreenBox grow light: on/off, brightness and colour temperature (3000-6000 K)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GreenBoxConfigEntry
from .entity import GreenBoxEntity
from .protocol import (
    MAX_KELVIN,
    MIN_KELVIN,
    REG_COLD,
    REG_MID,
    REG_POWER,
    REG_WARM,
    channels_from_light,
    light_from_channels,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GreenBoxConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GreenBoxLight(entry.runtime_data, "light")])


class GreenBoxLight(GreenBoxEntity, LightEntity):
    _attr_name = None
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = MIN_KELVIN
    _attr_max_color_temp_kelvin = MAX_KELVIN

    def _current(self) -> tuple[float, int]:
        d = self.coordinator.data
        return light_from_channels(d[REG_WARM], d[REG_MID], d[REG_COLD])

    @property
    def is_on(self) -> bool:
        return self.coordinator.data[REG_POWER] != 0

    @property
    def brightness(self) -> int:
        return round(self._current()[0] * 255 / 100)

    @property
    def color_temp_kelvin(self) -> int:
        return self._current()[1]

    async def async_turn_on(self, **kwargs: Any) -> None:
        values = {REG_POWER: 1}
        if ATTR_BRIGHTNESS in kwargs or ATTR_COLOR_TEMP_KELVIN in kwargs:
            percent, kelvin = self._current()
            if ATTR_BRIGHTNESS in kwargs:
                percent = max(1, kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN, kelvin)
            values |= channels_from_light(percent, kelvin)
        await self.coordinator.async_write(values)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write({REG_POWER: 0})
