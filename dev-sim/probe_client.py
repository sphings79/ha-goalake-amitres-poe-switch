"""Run the real API client against a switch. Start it yourself, the password comes from the environment.

    GOALAKE_PASSWORD='...' .venv/bin/python dev-sim/probe_client.py <ip> [port] [--wrong-password]

Reads the state twice over one session, logs out and prints a redacted summary (no password, session id,
serial, MAC or network settings). With --wrong-password it afterwards tries a bogus password once to
show how the device rejects it (empty reply or error code).
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiohttp  # noqa: E402

from custom_components.goalake_poe_switch import api  # noqa: E402


def show(data: api.SwitchData) -> None:
    print(f"firmware {data.firmware}  {data.voltage_v} V  total {data.total_power_w} W  {data.temperature_c} C")
    print("settings:", data.settings)
    for p in data.ports:
        print(
            f"  port {p.label:>4} idx {p.index}  poe={p.poe_enabled!s:5} power={p.power_w!s:5} "
            f"link={p.speed_mbps:>4}M tx={p.tx_kbps} rx={p.rx_kbps} admin={p.admin_enabled}"
        )


async def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    ip = args[0]
    port = int(args[1]) if len(args) > 1 else 80
    password = os.environ.get("GOALAKE_PASSWORD")
    if not password:
        print("GOALAKE_PASSWORD is not set")
        return 2

    async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar()) as http:
        c = api.GoalakeClient(http, ip, password, port=port)
        print("reachable (cmd 100, no login):", await c.check_reachable())
        try:
            for n in (1, 2):
                t = time.monotonic()
                data = await c.fetch_all()
                print(f"--- fetch {n}: {int((time.monotonic() - t) * 1000)} ms")
                if n == 1:
                    show(data)
        except Exception as exc:  # message of our own errors is safe, others only by type
            msg = str(exc) if isinstance(exc, api.GoalakeError) else ""
            print(f"ERROR {type(exc).__name__} {msg}")
        finally:
            await c.close()
            print("closed")

        if "--wrong-password" in sys.argv:
            bad = api.GoalakeClient(http, ip, "wrong-password-test", port=port)
            try:
                await bad.validate()
                print("wrong password: ACCEPTED (unexpected)")
            except Exception as exc:
                print(f"wrong password -> {type(exc).__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
