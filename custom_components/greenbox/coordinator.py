"""Connects to the GreenBox briefly, reads all registers, and sends commands.

The box accepts only one BLE connection at a time, so we never stay connected:
otherwise the phone app could no longer reach it.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .protocol import CHANNELS, CHAR_REGISTERS, REG_POWER, build_frame, parse_frame

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)
READ_TIMEOUT = 8.0
REQUIRED = (REG_POWER, *CHANNELS)

type GreenBoxConfigEntry = ConfigEntry[GreenBoxCoordinator]


class GreenBoxCoordinator(DataUpdateCoordinator[dict[str, int]]):
    def __init__(self, hass: HomeAssistant, entry: GreenBoxConfigEntry, address: str) -> None:
        super().__init__(
            hass, _LOGGER, config_entry=entry, name=f"GreenBox {address}", update_interval=UPDATE_INTERVAL
        )
        self.address = address
        self._lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, int]:
        try:
            return await self._session([])
        except Exception as err:  # noqa: BLE001 - BLE errors come in many shapes
            raise UpdateFailed(f"GreenBox not reachable: {err}") from err

    async def async_write(self, values: dict[str, int]) -> None:
        """Write registers (power last), then refresh state from the box's echo."""
        frames = [build_frame(reg, val) for reg, val in values.items() if reg != REG_POWER]
        if REG_POWER in values:
            frames.append(build_frame(REG_POWER, values[REG_POWER]))
        self.async_set_updated_data(await self._session(frames))

    async def _session(self, frames: list[bytes]) -> dict[str, int]:
        async with self._lock:
            device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
            if device is None:
                raise UpdateFailed("GreenBox not in Bluetooth range")
            client = await establish_connection(BleakClientWithServiceCache, device, device.name or "GreenBox")
            registers: dict[str, int] = {}
            done = asyncio.Event()
            sent = not frames

            def on_notify(_char, data: bytearray) -> None:
                parsed = parse_frame(bytes(data))
                if parsed is None:
                    return
                registers[parsed[0]] = parsed[1]
                # After a write, only trust values reported after the write went out.
                if sent and all(r in registers for r in REQUIRED) and len(registers) >= 12:
                    done.set()

            try:
                await client.start_notify(CHAR_REGISTERS, on_notify)
                for frame in frames:
                    await client.write_gatt_char(CHAR_REGISTERS, frame, response=False)
                if frames:
                    registers.clear()
                    sent = True
                try:
                    await asyncio.wait_for(done.wait(), READ_TIMEOUT)
                except TimeoutError:
                    if not all(r in registers for r in REQUIRED):
                        raise UpdateFailed(f"Incomplete data from GreenBox: {registers}") from None
            finally:
                await client.disconnect()
            return registers
