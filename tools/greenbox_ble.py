"""GreenBox BLE explorer.

  python3 greenbox_ble.py scan            # list nearby BLE devices, strongest first
  python3 greenbox_ble.py dump <address>  # connect and print all GATT services/characteristics
  python3 greenbox_ble.py listen <address> [seconds]  # subscribe to all notify characteristics
  python3 greenbox_ble.py snap <address> <label>      # decoded registers, appended to snapshots.log
  python3 greenbox_ble.py set <address> O=0 wait=5 O=1  # write registers (see docs/PROTOCOL.md)
"""
import asyncio
import sys

from bleak import BleakClient, BleakScanner


async def scan():
    devs = await BleakScanner.discover(timeout=15, return_adv=True)
    for d, a in sorted(devs.values(), key=lambda x: -x[1].rssi):
        mfr = {k: v.hex() for k, v in a.manufacturer_data.items()}
        print(f"{a.rssi:>4}  {d.address}  {a.local_name or d.name or '-'}  uuids={a.service_uuids}  mfr={mfr}")


async def dump(address):
    async with BleakClient(address, timeout=20) as c:
        for s in c.services:
            print(f"[service] {s.uuid}  {s.description}")
            for ch in s.characteristics:
                line = f"   [char] {ch.uuid}  handle={ch.handle}  props={','.join(ch.properties)}"
                if "read" in ch.properties:
                    try:
                        v = await c.read_gatt_char(ch)
                        line += f"  value={v.hex()}  ascii={v.decode(errors='replace')!r}"
                    except Exception as e:
                        line += f"  read-error={e}"
                print(line)


async def listen(address, seconds=60):
    async with BleakClient(address, timeout=20) as c:
        def cb(ch, data):
            print(f"{ch.uuid}  {data.hex()}")
        for s in c.services:
            for ch in s.characteristics:
                if "notify" in ch.properties or "indicate" in ch.properties:
                    await c.start_notify(ch, cb)
                    print(f"subscribed {ch.uuid}")
        await asyncio.sleep(seconds)


STATE_CHARS = ["0000ff03-0000-1000-8000-00805f9b34fb",
               "0000ff05-0000-1000-8000-00805f9b34fb",
               "0000ff06-0000-1000-8000-00805f9b34fb"]


async def snap(address, label):
    """Read the state characteristics plus 5 s of notifications, append to snapshots.log."""
    import datetime
    lines = []
    async with BleakClient(address, timeout=20) as c:
        def cb(ch, data):
            lines.append(f"  notify {ch.uuid[4:8]}  {data.hex()}  {data.decode(errors='replace')!r}")
        for u in STATE_CHARS:
            v = await c.read_gatt_char(u)
            lines.append(f"  read   {u[4:8]}  {v.hex()}  {v.decode(errors='replace')!r}")
        for u in STATE_CHARS:
            try:
                await c.start_notify(u, cb)
            except Exception as e:
                lines.append(f"  (no notify on {u[4:8]}: {e.__class__.__name__})")
        await asyncio.sleep(5)
    regs = {}
    for line in lines:
        for f in __import__("re").findall(r"ee[0-9a-f]{8}ef", line):
            b = bytes.fromhex(f)
            if sum(b[:5]) & 0xFF == 0x11:  # EE + reg + hi + lo + chk
                regs[chr(b[1])] = (b[2] << 8) | b[3]
    summary = "  REGS  " + "  ".join(f"{k}={v}" for k, v in sorted(regs.items()))
    out = f"=== {datetime.datetime.now():%H:%M:%S}  {label}\n" + summary + "\n" + "\n".join(lines[:4]) + "\n"
    print(out)
    with open("snapshots.log", "a") as f:
        f.write(out)


def frame(reg, value):
    """EE <reg> <hi> <lo> <chk> EF, where all bytes up to chk sum to 0x11."""
    body = bytes([0xEE, ord(reg), (value >> 8) & 0xFF, value & 0xFF])
    return body + bytes([(0x11 - sum(body)) & 0xFF, 0xEF])


async def setseq(address, steps):
    """steps: list of 'REG=VALUE' or 'wait=SECONDS'; prints O/1/2/3 notifications along the way."""
    async with BleakClient(address, timeout=20) as c:
        def cb(ch, data):
            if len(data) == 6 and chr(data[1]) in "O123":
                print(f"  <- {chr(data[1])}={(data[2] << 8) | data[3]}")
        await c.start_notify(STATE_CHARS[1], cb)
        for step in steps:
            k, v = step.split("=")
            if k == "wait":
                await asyncio.sleep(float(v))
            else:
                f = frame(k, int(v))
                print(f"-> {k}={v}  {f.hex()}")
                await c.write_gatt_char(STATE_CHARS[1], f, response=False)
        await asyncio.sleep(3)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "set":
        asyncio.run(setseq(sys.argv[2], sys.argv[3:]))
        sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "snap":
        asyncio.run(snap(sys.argv[2], " ".join(sys.argv[3:]) or "-"))
        sys.exit()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        asyncio.run(scan())
    elif cmd == "dump":
        asyncio.run(dump(sys.argv[2]))
    elif cmd == "listen":
        asyncio.run(listen(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 60))
