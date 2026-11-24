"""Write tests for the remaining commands on a real switch, in small reversible groups. Run it yourself.

    GOALAKE_PASSWORD='...' .venv/bin/python dev-sim/probe_write_more.py <ip> --group settings --yes
    GOALAKE_PASSWORD='...' .venv/bin/python dev-sim/probe_write_more.py <ip> --group warn --yes
    GOALAKE_PASSWORD='...' .venv/bin/python dev-sim/probe_write_more.py <ip> --group port --port-label 2 --yes
    GOALAKE_PASSWORD='...' .venv/bin/python dev-sim/probe_write_more.py <ip> --group restart --port-label 1 --yes

    GOALAKE_PASSWORD='...' .venv/bin/python dev-sim/probe_write_more.py <ip> --group reboot --yes

Groups: settings = LLDP, storm control, PoE watchdog, auto extend (each is switched and switched back);
        warn     = total power warning threshold (set to 100 W, then back);
        port     = flow control, priority, upload and download limit of one PoE port (changed, then back);
        restart  = power-cycles one PoE port (the connected device loses power for a few seconds);
        reboot   = restarts the whole switch (EVERY PoE device loses power, the switch is away for about a minute).
Every test reads the state, writes, reads back, restores the original value (also after an error) and says OK or
MISMATCH. The password is never printed. Without --yes nothing is changed.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiohttp  # noqa: E402

from custom_components.goalake_poe_switch import api  # noqa: E402

SETTLE = 2.0


def err_text(exc: Exception) -> str:
    return f"{type(exc).__name__} {exc}" if isinstance(exc, api.GoalakeError) else type(exc).__name__


async def check(c: api.GoalakeClient, name: str, read, write_new, write_back, expect) -> None:
    """read(data) -> value; write_new() / write_back() are coroutine factories."""
    before = read(await c.fetch_all())
    try:
        await write_new()
        await asyncio.sleep(SETTLE)
        after = read(await c.fetch_all())
        verdict = "OK" if after == expect else f"MISMATCH (expected {expect})"
        print(f"{name:26s} {before!s:>8} -> {after!s:<8} {verdict}")
    except Exception as exc:  # keep going: the restore below still has to run
        print(f"{name:26s} ERROR {err_text(exc)}")
    finally:
        try:
            await write_back()
            await asyncio.sleep(SETTLE)
            back = read(await c.fetch_all())
            print(f"{'  restore':26s} {'':>8}    {back!s:<8} {'OK' if back == before else f'NOT RESTORED (was {before})'}")
        except Exception as exc:
            print(f"{'  restore':26s} FAILED {err_text(exc)} (original value: {before})")


async def group_settings(c: api.GoalakeClient) -> None:
    for key, name, setter in (
        ("lldp", "LLDP", c.set_lldp),
        ("storm", "storm control", c.set_storm),
        ("watchdog", "PoE watchdog", c.set_watchdog),
        ("ai_auto_extend", "auto extend", c.set_ai_auto_extend),
    ):
        current = (await c.fetch_all()).settings.get(key)
        if current is None:
            print(f"{name:26s} not reported by the device, skipped")
            continue
        new = not bool(current)
        await check(
            c, name, lambda d, k=key: d.settings.get(k),
            lambda s=setter, n=new: s(n), lambda s=setter, o=bool(current): s(o), int(new),
        )


async def group_warn(c: api.GoalakeClient) -> None:
    original = (await c.fetch_all()).settings.get("power_warn")
    new = 100 if original != 100 else 90
    await check(c, "power warning (W)", lambda d: d.settings.get("power_warn"),
                lambda: c.set_power_warn(new), lambda: c.set_power_warn(int(original or 0)), new)


async def group_port(c: api.GoalakeClient, label: str) -> None:
    data = await c.fetch_all()
    port = next((p for p in data.ports if p.label == label and p.is_poe), None)
    if port is None:
        print(f"port {label} is not a PoE port")
        return
    i = port.index

    def at(arr, idx):
        return arr[idx]

    flow, prio = list(data.flow), list(data.priority)
    up, down = list(data.limit_up), list(data.limit_down)

    def with_(arr, value):
        out = list(arr)
        out[i] = value
        return out

    new_flow = 0 if flow[i] else 1
    await check(c, f"flow control port {label}", lambda d: at(d.flow, i),
                lambda: c.set_flow(with_(flow, new_flow)), lambda: c.set_flow(flow), new_flow)
    new_prio = 3 if prio[i] != 3 else 2
    await check(c, f"priority port {label}", lambda d: at(d.priority, i),
                lambda: c.set_priority(with_(prio, new_prio)), lambda: c.set_priority(prio), new_prio)
    new_up = 50 * api.LIMIT_FACTOR
    await check(c, f"upload limit port {label}", lambda d: at(d.limit_up, i),
                lambda: c.set_limits(with_(up, new_up), down), lambda: c.set_limits(up, down), new_up)
    new_down = 50 * api.LIMIT_FACTOR
    await check(c, f"download limit port {label}", lambda d: at(d.limit_down, i),
                lambda: c.set_limits(up, with_(down, new_down)), lambda: c.set_limits(up, down), new_down)


async def group_restart(c: api.GoalakeClient, label: str) -> None:
    data = await c.fetch_all()
    port = next((p for p in data.ports if p.label == label and p.is_poe), None)
    if port is None:
        print(f"port {label} is not a PoE port")
        return
    print(f"before : poe={port.poe_enabled} power={port.power_w} W link={port.speed_mbps}M")
    await c.restart_port(port.index)  # raises unless the device acknowledges
    print("restart command acknowledged")
    for wait in (2, 6, 10):
        await asyncio.sleep(wait if wait == 2 else 4)
        p = next(x for x in (await c.fetch_all()).ports if x.index == port.index)
        print(f"+{wait:>2}s   : poe={p.poe_enabled} power={p.power_w} W link={p.speed_mbps}M")


async def group_reboot(c: api.GoalakeClient) -> None:
    import time

    before = await c.fetch_all()
    linked = sum(1 for p in before.ports if p.connected)
    print(f"before : firmware {before.firmware}, {before.temperature_c} C, {linked} ports linked, lldp={before.settings.get('lldp')}")
    started = time.monotonic()
    await c.reboot()  # sent once, a dropped connection counts as sent
    print("reboot command sent")
    down_at = up_at = None
    while time.monotonic() - started < 180:
        reachable = await c.check_reachable()
        elapsed = int(time.monotonic() - started)
        if reachable and down_at is None and elapsed > 40:
            print(f"+{elapsed:>3}s : the switch never went away, the reboot did not happen")
            return
        if not reachable and down_at is None:
            down_at = elapsed
            print(f"+{elapsed:>3}s : switch is down")
        if reachable and down_at is not None:
            up_at = elapsed
            print(f"+{elapsed:>3}s : switch answers again")
            break
        await asyncio.sleep(3)
    if up_at is None:
        print("the switch did not come back within 180 s")
        return
    await asyncio.sleep(5)
    after = await c.fetch_all()
    linked_after = sum(1 for p in after.ports if p.connected)
    print(f"after  : firmware {after.firmware}, {after.temperature_c} C, {linked_after} ports linked, lldp={after.settings.get('lldp')}, "
          f"poe port 1 on={next(p for p in after.ports if p.label == '1').poe_enabled}")
    print(f"settings kept: {'yes' if after.settings == before.settings else 'NO, differences: ' + str({k: (before.settings.get(k), v) for k, v in after.settings.items() if before.settings.get(k) != v})}")


async def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("--") or "--group" not in args:
        print(__doc__)
        return 2
    ip = args[0]
    group = args[args.index("--group") + 1]
    label = args[args.index("--port-label") + 1] if "--port-label" in args else "2"
    password = os.environ.get("GOALAKE_PASSWORD")
    if not password:
        print("GOALAKE_PASSWORD is not set")
        return 2
    if group not in ("settings", "warn", "port", "restart", "reboot"):
        print("unknown group")
        return 2
    if "--yes" not in args:
        print(f"dry run: group '{group}' would change values on {ip} and restore them; add --yes to run it")
        return 0
    async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar()) as http:
        c = api.GoalakeClient(http, ip, password)
        try:
            if group == "settings":
                await group_settings(c)
            elif group == "warn":
                await group_warn(c)
            elif group == "port":
                await group_port(c, label)
            elif group == "reboot":
                await group_reboot(c)
            else:
                await group_restart(c, label)
        except Exception as exc:
            print(f"ERROR {err_text(exc)}")
            return 1
        finally:
            await c.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
