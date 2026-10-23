"""GreenBox BLE protocol (reverse-engineered, see docs/PROTOCOL.md).

Everything goes through characteristic ff05 as 6-byte frames:

    EE <register, ASCII> <value hi> <value lo> <checksum> EF

All bytes from EE up to and including the checksum sum to 0x11 (mod 256).
While a client is connected the box cycles through all registers as notifications;
writing the same frame sets a register.
"""

from __future__ import annotations

CHAR_REGISTERS = "0000ff05-0000-1000-8000-00805f9b34fb"

REG_STATUS = "O"  # bit 0: light on, bit 1: water present (read-only, set by the box)
REG_WARM = "1"
REG_MID = "2"
REG_COLD = "3"
CHANNELS = (REG_WARM, REG_MID, REG_COLD)
REG_WATER = "W"  # 0 = sensor dry, 100 = sensor in water
REG_WEEKDAY_START = "S"  # light on time, HHMM in UTC
REG_WEEKDAY_HOURS = "D"  # light duration in hours
REG_WEEKEND_START = "s"
REG_WEEKEND_HOURS = "d"  # 0 = weekend uses no separate schedule

STATUS_LIGHT = 0x01

# Registers whose meaning is still unknown; exposed as diagnostic sensors.
UNKNOWN_REGISTERS = ("T", "f", "r")

MIN_KELVIN = 3000
MAX_KELVIN = 6000

# The app does not allow less than 12 hours of light.
MIN_HOURS = 12
MAX_HOURS = 24

# Light presets of the official app: name -> (warm, mid, cold).
# "medium" (neutral, 50 %) is inferred from the other presets, not captured.
PRESETS = {
    "growth": (100, 100, 100),
    "medium": (50, 50, 50),
    "ambient": (99, 0, 0),
    "night_light": (0, 0, 15),
}


def build_frame(register: str, value: int) -> bytes:
    body = bytes([0xEE, ord(register), (value >> 8) & 0xFF, value & 0xFF])
    return body + bytes([(0x11 - sum(body)) & 0xFF, 0xEF])


def parse_frame(data: bytes) -> tuple[str, int] | None:
    if len(data) != 6 or data[0] != 0xEE or data[5] != 0xEF:
        return None
    if sum(data[:5]) & 0xFF != 0x11:
        return None
    return chr(data[1]), (data[2] << 8) | data[3]


def channels_from_light(percent: float, kelvin: int) -> dict[str, int]:
    """Spread brightness over the three LED channels.

    Observed in the app: warm = only channel 1, neutral = all three equal,
    cold = only channel 3, and channel sum / 3 = brightness in percent.
    Colour temperatures in between are interpolated linearly (assumption).
    """
    p = min(max((kelvin - MIN_KELVIN) / (MAX_KELVIN - MIN_KELVIN), 0.0), 1.0)
    if p <= 0.5:
        weights = (1.0, 2 * p, 2 * p)
    else:
        weights = (2 * (1 - p), 2 * (1 - p), 1.0)
    scale = 3 * percent / sum(weights)
    return {reg: min(100, round(w * scale)) for reg, w in zip(CHANNELS, weights)}


def light_from_channels(warm: int, mid: int, cold: int) -> tuple[float, int]:
    """Inverse of channels_from_light: returns (percent, kelvin)."""
    percent = (warm + mid + cold) / 3
    if warm == cold == 0:
        p = 0.5
    elif warm >= cold:
        p = (cold / warm) / 2
    else:
        p = 1 - (warm / cold) / 2
    return percent, round(MIN_KELVIN + p * (MAX_KELVIN - MIN_KELVIN))
