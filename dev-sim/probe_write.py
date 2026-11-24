"""Write tests on a real switch for one PoE port. Run it yourself.

    GOALAKE_PASSWORD='...' .venv/bin/python dev-sim/probe_write.py <ip> --port-label 1 --yes            # PoE off, then on
    GOALAKE_PASSWORD='...' .venv/bin/python dev-sim/probe_write.py <ip> --port-label 1 --extend --yes   # 10M extend mode, then back

Reads the state, changes the port (PoE off, or with --extend the 10M port mode), waits, reads back and then
restores the original value (always, also after an error). Connected devices lose power (PoE) or negotiate a new
link speed (extend) for a few seconds. The password is
never printed. Without --yes nothing is changed.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiohttp  # noqa: E402

from custom_components.goalake_poe_switch import api  # noqa: E402


def line(data: api.SwitchData, label: str) -> str:
    p = next(x for x in data.ports if x.label == label)
    mode = api.PORT_MODES.get(p.phy_mode, p.phy_mode)
    return f"port {label} (idx {p.index}): poe={p.poe_enabled} power={p.power_w} W link={p.speed_mbps}M mode={mode}"


async def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print(__doc__)
        return 2
    ip = args[0]
    label = args[args.index("--port-label") + 1] if "--port-label" in args else "1"
    password = os.environ.get("GOALAKE_PASSWORD")
    if not password:
        print("GOALAKE_PASSWORD is not set")
        return 2
    async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar()) as http:
        c = api.GoalakeClient(http, ip, password)
        try:
            data = await c.fetch_all()
            port = next((x for x in data.ports if x.label == label and x.is_poe), None)
            if port is None:
                print(f"port {label} is not a PoE port")
                return 2
            print("before :", line(data, label))
            if "--yes" not in args:
                print("dry run, add --yes to change the port")
                return 0
            if "--extend" in args:
                original = port.phy_mode
                try:
                    await c.set_port_mode(port.index, api.MODE_EXTEND)
                    await asyncio.sleep(8)
                    print("extend :", line(await c.fetch_all(), label))
                finally:
                    await c.set_port_mode(port.index, original)
                    await asyncio.sleep(8)
                    print("restored:", line(await c.fetch_all(), label))
                return 0
            was_on = bool(port.poe_enabled)
            try:
                await c.set_poe(port.index, False)
                await asyncio.sleep(4)
                print("off    :", line(await c.fetch_all(), label))
            finally:
                await c.set_poe(port.index, was_on)
                await asyncio.sleep(6)
                print("restored:", line(await c.fetch_all(), label))
        except Exception as exc:
            msg = str(exc) if isinstance(exc, api.GoalakeError) else ""
            print(f"ERROR {type(exc).__name__} {msg}")
            return 1
        finally:
            await c.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
