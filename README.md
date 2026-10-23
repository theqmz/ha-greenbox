# GreenBox for Home Assistant (unofficial)

Control the light of a [BerlinGreen GreenBox](https://berlingreen.com) indoor garden from Home Assistant over Bluetooth. Fully local, no cloud, no account.

> **Unofficial.** This project is not made by or affiliated with BerlinGreen. The Bluetooth protocol was reverse-engineered from one box (see [docs/PROTOCOL.md](docs/PROTOCOL.md)). Use at your own risk.

## Features

- **Light** with on/off, brightness and colour temperature (3000–6000 K), usable in automations and scenes like any other light.
- **Diagnostic sensors** with the raw values of registers that are not decoded yet. They are meant to help find the water level and schedule; reports are welcome.
- Discovered automatically as soon as Home Assistant sees the box over Bluetooth.

## Requirements

- Home Assistant 2025.2 or newer, with a Bluetooth adapter or an [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html) within range of the box.
- Tested with the GreenBox (not the Plus). Other models or firmware versions may behave differently; please open an issue with the values of the diagnostic sensors.

## Installation

### HACS

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/theqmz/ha-greenbox`, category **Integration**.
2. Install **GreenBox (BerlinGreen, unofficial)** and restart Home Assistant.

### Manual

Copy `custom_components/greenbox` into the `custom_components` folder of your Home Assistant configuration and restart.

## Setup

The box shows up under **Settings → Devices & services → Discovered**. If not, add the integration **GreenBox** manually and pick the box from the list.

## Good to know

- The box accepts only **one** Bluetooth connection at a time. The integration therefore connects only briefly: every 5 minutes to read the state, and for each command. The official app keeps working; only during those few seconds it cannot connect, and while the app is open, Home Assistant cannot reach the box.
- With warm light only one of the three LED channels is on, so warm light reaches at most about 33 % brightness. The app behaves the same way.
- Colour temperatures between warm, neutral and cold are interpolated; they may differ slightly from the app.

## Contributing

To decode more of the protocol, see [docs/PROTOCOL.md](docs/PROTOCOL.md) and the small tool in [`tools/`](tools/). Especially wanted: water level, schedule, and the GreenBox Plus.

## License

[MIT](LICENSE)
