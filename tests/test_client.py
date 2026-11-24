"""Client tests against the in-process mock switch (dev-sim/mock_switch.py).

These need real sockets, which the Home Assistant pytest plugin blocks. Run them with the plugin
disabled: pytest -p no:homeassistant tests/test_client.py (see scripts/test.sh).
"""

from __future__ import annotations

import importlib.util
import logging
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import aiohttp
import pytest

from custom_components.goalake_poe_switch import api

SIM_PATH = Path(__file__).parent.parent / "dev-sim" / "mock_switch.py"
PASSWORD = "S3cret-Pw!x"
_spec = importlib.util.spec_from_file_location("mock_switch", SIM_PATH)
mock_switch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mock_switch)


@pytest.fixture
def start_sim():
    servers = []

    def _start(fail_mode: str = "none"):
        st = mock_switch.State(PASSWORD, fail_mode)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), mock_switch.make_handler(st))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
        return st, srv.server_address[1]

    yield _start
    for srv in servers:
        srv.shutdown()
        srv.server_close()


@pytest.fixture
async def http():
    async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar()) as session:
        yield session


def client(http, port, password=PASSWORD):
    return api.GoalakeClient(http, "127.0.0.1", password, port=port, timeout=3)


async def test_fetch_all_parses_ports_and_values(start_sim, http):
    _, port = start_sim()
    c = client(http, port)
    data = await c.fetch_all()
    assert data.firmware == "6.1.260430"
    assert data.voltage_v == 52.4
    assert data.total_power_w == 1.3  # tp is mW
    assert data.temperature_c == 38.2
    by_label = {p.label: p for p in data.ports}
    assert len(data.ports) == 10
    # port 1 is array index 7; the fixture has a PoE device there (1.3 W, 100M)
    p1 = by_label["1"]
    assert (p1.index, p1.is_poe, p1.power_w, p1.speed_mbps, p1.connected) == (7, True, 1.3, 100, True)
    assert by_label["2"].index == 6 and by_label["8"].index == 0
    assert by_label["LAN1"].index == 9 and by_label["LAN1"].speed_mbps == 1000
    assert by_label["LAN2"].index == 8 and not by_label["LAN2"].connected
    assert by_label["LAN1"].is_poe is False and by_label["LAN1"].power_w is None
    assert data.settings["lldp"] == 1 and data.netcfg["dhcp"] == 1
    await c.close()


async def test_session_is_reused(start_sim, http):
    st, port = start_sim()
    c = client(http, port)
    for _ in range(3):
        await c.fetch_all()
    assert st.logins == 1
    await c.close()


async def test_wrong_password(start_sim, http):
    _, port = start_sim()
    c = client(http, port, "wrong-pw-123")
    with pytest.raises(api.InvalidAuth) as exc:
        await c.validate()
    assert "wrong-pw-123" not in str(exc.value)


async def test_relogin_after_session_loss(start_sim, http):
    st, port = start_sim("expire")  # the device drops the session on every 5th request
    c = client(http, port)
    for _ in range(12):
        await c.fetch_all()
    assert st.logins >= 2


async def test_empty_reply_backs_off(start_sim, http):
    st, port = start_sim("empty")
    c = client(http, port)
    with pytest.raises(api.CannotConnect):
        await c.fetch_all()
    seen = st.requests
    with pytest.raises(api.CannotConnect):
        await c.fetch_all()
    assert st.requests == seen  # the second call did not touch the device


async def test_check_reachable_needs_no_login(start_sim, http):
    st, port = start_sim()
    assert await client(http, port).check_reachable() is True
    assert st.logins == 0


async def test_unreachable(http):
    c = api.GoalakeClient(http, "127.0.0.1", PASSWORD, port=1, timeout=2)
    assert await c.check_reachable() is False
    with pytest.raises(api.CannotConnect):
        await c.fetch_all()


async def test_no_secrets_in_logs(start_sim, http, caplog):
    caplog.set_level(logging.DEBUG)
    st, port = start_sim()
    c = client(http, port)
    data = await c.fetch_all()
    sid = c._sid
    assert sid
    assert PASSWORD not in repr(c)
    await c.close()
    wrong = client(http, port, "wrong-pw-123")
    with pytest.raises(api.InvalidAuth):
        await wrong.validate()
    logs = caplog.text
    assert logs  # something was logged at all
    for secret in (PASSWORD, "wrong-pw-123", sid, data.serial, data.mac):
        assert secret not in logs


async def test_is_switch(start_sim, http):
    _, port = start_sim()
    assert await client(http, port).is_switch() is True


def test_model_from_serial():
    assert api.model_from_serial("GPS208000000000SIMULATED00") == "GPS208"
    assert api.model_from_serial("") is None
    assert api.model_from_serial("xyz") is None


async def test_writes_change_the_device(start_sim, http):
    st, port = start_sim()
    c = client(http, port)
    await c.fetch_all()
    # PoE off on port 1 (array index 7): opcode 0 << 9 | 7 << 4 | 2
    await c.set_poe(7, False)
    assert st.data["detail"]["poec"][7] == 0 and st.data["detail"]["pw"][7] == "0"
    await c.set_poe(7, True)
    assert st.data["detail"]["poec"][7] == 1
    await c.set_port_mode(6, 4)
    assert st.data["detail"]["phyc"][6] == 4
    await c.set_lldp(False)
    await c.set_storm(True)
    await c.set_watchdog(True)
    await c.set_ai_auto_extend(True)
    await c.set_power_warn(90)
    assert st.data["lldp"] == {"lldp": 0} and st.data["storm"] == {"storm": 1}
    assert st.data["AI_Wdog"] == {"AI_Wdog": 1} and st.data["AI_AnAuto"] == {"AI_AnAuto": 1}
    assert st.data["PoWarn"] == {"PoWarn": 90}
    flow = [1] * 10
    flow[3] = 0
    await c.set_flow(flow)
    prio = [0] * 10
    prio[2] = 3
    await c.set_priority(prio)
    await c.set_limits([0] * 9 + [10240], [0] * 10)
    assert st.data["flow"]["flow"][3] == 0 and st.data["PortPri"]["PortPri"][2] == 3
    assert st.data["limit"]["up"][9] == 10240
    data = await c.fetch_all()
    assert data.flow[3] == 0 and data.priority[2] == 3 and data.limit_up[9] == 10240
    await c.reboot()
    with pytest.raises(ValueError):
        await c.set_port_mode(0, 9)
    await c.close()


async def test_poe_opcode_matches_the_web_ui(start_sim, http):
    """opcode = value << 9 | index << 4 | kind; the old sscpoe integration used (0x202 | idx << 4) for PoE on."""
    st, port = start_sim()
    c = client(http, port)
    sent = []
    orig = c._request

    async def spy(cmd, calldata=None):
        sent.append((cmd, calldata))
        return await orig(cmd, calldata)

    c._request = spy
    await c.set_poe(7, True)
    await c.set_poe(7, False)
    assert sent == [(103, {"opcode": 0x202 | 7 << 4}), (103, {"opcode": 2 | 7 << 4})]
    await c.close()


@pytest.mark.parametrize("drops", [False, True])
async def test_reboot_is_sent_exactly_once(start_sim, http, drops):
    st, port = start_sim()
    st.reboot_drops = drops  # the device may or may not answer before it restarts
    c = client(http, port)
    await c.fetch_all()
    requests_before = st.requests
    await c.reboot()  # must not raise either way
    assert st.reboots == 1  # never resent
    assert st.requests == requests_before + 1  # no login, no retry
    # the old session is dropped; a new login happens on the next use
    await c.fetch_all()
    assert st.logins == 2
    await c.close()
