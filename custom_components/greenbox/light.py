"""GreenBox grow light: on/off, brightness, colour temperature (3000-6000 K) and the app's presets."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GreenBoxConfigEntry
from .entity import GreenBoxEntity
from .protocol import (
    CHANNELS,
    MAX_KELVIN,
    MIN_KELVIN,
    PRESETS,
    REG_COLD,
    REG_MID,
    REG_STATUS,
    REG_WARM,
    STATUS_LIGHT,
    channels_from_light,
    light_from_channels,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GreenBoxConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GreenBoxLight(entry.runtime_data, "light")])


class GreenBoxLight(GreenBoxEntity, LightEntity):
    _attr_name = None
    _attr_translation_key = "light"
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(PRESETS)
    _attr_min_color_temp_kelvin = MIN_KELVIN
    _attr_max_color_temp_kelvin = MAX_KELVIN

    def _channels(self) -> tuple[int, int, int]:
        d = self.coordinator.data
        return d[REG_WARM], d[REG_MID], d[REG_COLD]

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data[REG_STATUS] & STATUS_LIGHT)

    @property
    def brightness(self) -> int:
        return round(light_from_channels(*self._channels())[0] * 255 / 100)

    @property
    def color_temp_kelvin(self) -> int:
        return light_from_channels(*self._channels())[1]

    @property
    def effect(self) -> str | None:
        channels = self._channels()
        return next((name for name, preset in PRESETS.items() if preset == channels), None)

    async def async_turn_on(self, **kwargs: Any) -> None:
        values = {REG_STATUS: 1}
        if ATTR_EFFECT in kwargs:
            values |= dict(zip(CHANNELS, PRESETS[kwargs[ATTR_EFFECT]]))
        elif ATTR_BRIGHTNESS in kwargs or ATTR_COLOR_TEMP_KELVIN in kwargs:
            percent, kelvin = light_from_channels(*self._channels())
            if ATTR_BRIGHTNESS in kwargs:
                percent = max(1, kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN, kelvin)
            values |= channels_from_light(percent, kelvin)
        await self.coordinator.async_write(values)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write({REG_STATUS: 0})
