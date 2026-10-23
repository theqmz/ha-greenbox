"""GreenBox BLE protocol (reverse-engineered, see docs/PROTOCOL.md).

Everything goes through characteristic ff05 as 6-byte frames:

    EE <register, ASCII> <value hi> <value lo> <checksum> EF

All bytes from EE up to and including the checksum sum to 0x11 (mod 256).
While a client is connected the box cycles through all registers as notifications;
writing the same frame sets a register.
"""

from __future__ import annotations

CHAR_REGISTERS = "0000ff05-0000-1000-8000-00805f9b34fb"

REG_POWER = "O"
REG_WARM = "1"
REG_MID = "2"
REG_COLD = "3"
CHANNELS = (REG_WARM, REG_MID, REG_COLD)

# Registers whose meaning is still unknown; exposed as diagnostic sensors.
UNKNOWN_REGISTERS = ("D", "S", "T", "W", "d", "f", "r", "s")

MIN_KELVIN = 3000
MAX_KELVIN = 6000


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
