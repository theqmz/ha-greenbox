# GreenBox BLE protocol

Reverse-engineered from one GreenBox (not the Plus) by comparing the box's state before and after changes in the official app. Nothing here comes from the manufacturer; other firmware versions may differ.

## Device

- ESP32. Advertises as `GreenBox` followed by the last part of its MAC, with service UUID `0x00FF`.
- Accepts only **one** BLE connection at a time. While the app is connected, nothing else can connect, and the other way round.
- No pairing or encryption.

## Characteristics (service `000000ff-0000-1000-8000-00805f9b34fb`)

| UUID | Properties | Content |
|---|---|---|
| `ff01` | read, write, notify | JSON list of nearby Wi-Fi networks, e.g. `[["MyWifi",0], …]` |
| `ff02` | read, write, notify | empty; probably where Wi-Fi credentials go (not tested) |
| `ff03` | read, notify | `["d"]`; probably Wi-Fi status ("disconnected") |
| `ff05` | read, notify, write without response | **register frames, see below** (all control goes through here) |
| `ff06` | read, write | `0,0,0`; meaning unknown. Notify is advertised but fails. |

The Wi-Fi characteristics suggest that the announced network feature is partly implemented in the firmware. It is not used by this integration.

## Register frames (`ff05`)

Every frame is 6 bytes:

```
EE  <register>  <value hi>  <value lo>  <checksum>  EF
```

- `register` is a single ASCII character.
- `value` is a 16-bit big-endian integer.
- `checksum` is chosen so that all bytes from `EE` up to and including the checksum sum to `0x11` (mod 256):
  `checksum = (0x11 - (0xEE + register + hi + lo)) & 0xFF`

Example: `EE 4F 00 01 D3 EF` sets register `O` to 1.

While a client is connected and subscribed to `ff05`, the box sends every register as a notification, in a loop. Writing a frame to `ff05` sets that register, and the new value shows up in the next round of notifications.

## Registers

| Register | Values | Meaning |
|---|---|---|
| `O` | bit field | Bit 0: light on. Bit 1: water present (set by the box). Seen: 0, 1, 3. Write 0 or 1 to switch the light. |
| `1` | 0–100 | LED channel warm |
| `2` | 0–100 | LED channel middle |
| `3` | 0–100 | LED channel cold |
| `W` | 0 / 100 | Water sensor: 0 = dry, 100 = in water. Only wet/dry, no level. Seemed to react slowly when the sensor was taken out. |
| `S` | HHMM | Weekday schedule: light on time in **UTC** (700 = 07:00 UTC = 09:00 CEST) |
| `D` | hours | Weekday schedule: light duration (the app allows 12 or more) |
| `s` | HHMM | Weekend schedule: light on time in UTC |
| `d` | hours | Weekend schedule: light duration; 0 = no separate weekend schedule |
| `T` | 255 | unknown |
| `f` | 3 | unknown (firmware version?) |
| `r` | 1 | unknown (firmware revision?) |

Because the schedule is stored in UTC, the local on time shifts by one hour when daylight saving time changes, unless the app or Home Assistant writes it again. How the box knows the current time is not known yet.

### Light presets in the app

| App preset | `1` | `2` | `3` |
|---|---|---|---|
| Growth, neutral, 100 % | 100 | 100 | 100 |
| Ambient, warm (3000 K), 33 % | 99 | 0 | 0 |
| Night light, cold (6000 K), 5 % | 0 | 0 | 15 |
| Medium, neutral, 50 % | 50 | 50 | 50 (inferred, not captured) |

So the brightness in percent is the channel sum divided by 3. Warm uses only channel 1, cold only channel 3, and neutral all three equally. The integration interpolates linearly for the colour temperatures in between; how the app mixes 3700 K and 5300 K has not been checked yet.

## Exploring your own box

[`tools/greenbox_ble.py`](../tools/greenbox_ble.py) needs Python and `pip install bleak`. On macOS, run it from Terminal so it can ask for Bluetooth permission. Close the app first.

```
python3 tools/greenbox_ble.py scan                    # find the box
python3 tools/greenbox_ble.py dump <address>          # list characteristics and values
python3 tools/greenbox_ble.py snap <address> <label>  # decoded registers, appended to snapshots.log
python3 tools/greenbox_ble.py set <address> O=0 wait=5 O=1
```

To find out what a register means, run `snap`, change one thing in the app, close the app, and run `snap` again.
