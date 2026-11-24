"""Async client for the Goalake / Amitres PoE switch local web API.

Design rules (see docs/protocol.md):
  * The device allows one session at a time: this client holds exactly one session,
    reuses it for every request and logs out on close().
  * An empty reply means "no session / device busy": log in again once, then back off.
  * Secrets (password, session id, serial number, MAC) are never logged. Only the command
    number, the outcome and the duration reach the log.

Pass an aiohttp session without cookie handling (aiohttp.DummyCookieJar), the session id is
sent explicitly by this client so devices never share cookies.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

CMD_STATE = 100
CMD_ALL = 200
CMD_LOGIN = 123
CMD_LOGOUT = 126
CMD_PORT = 103  # PoE / port mode / port restart, opcode = value << 9 | port_index << 4 | kind
CMD_REBOOT = 104
CMD_LIMIT = 106
CMD_STORM = 107
CMD_LLDP = 127
CMD_AI_AUTO_EXTEND = 129
CMD_WATCHDOG = 130
CMD_FLOW = 133
CMD_PRIORITY = 138
CMD_POWER_WARN = 140

# opcode kinds of cmd 103 (from the web UI)
KIND_MODE = 0
KIND_POE = 2
KIND_RESTART = 3

# port mode values (web UI): 0 down, 1/2 10M half/full, 3/4 100M half/full, 5 1000M full
PORT_MODES = {0: "down", 1: "10m_half", 2: "10m_full", 3: "100m_half", 4: "100m_full", 5: "1000m_full"}

# "Extend" (long cable mode) is port mode 10M full duplex; switching it off restores the factory mode 1000M full (auto)
MODE_EXTEND = 2
MODE_DEFAULT = 5

# rate limits are sent in kbit/s, the web UI takes Mbit/s and multiplies by 1024
LIMIT_FACTOR = 1024

BACKOFF_START = 30.0
BACKOFF_MAX = 300.0

# link code -> speed in Mbit/s (web UI: 1/2 = 10M, 3/4 = 100M, 5 = 1000M)
LINK_SPEED = {0: 0, 1: 10, 2: 10, 3: 100, 4: 100, 5: 1000}

# errcode values seen for a rejected login
_AUTH_ERRCODES = {1009, 20004}


class GoalakeError(Exception):
    """Base error."""


class CannotConnect(GoalakeError):
    """Device unreachable, closed the connection without reply, or we are backing off."""


class InvalidAuth(GoalakeError):
    """The device rejected the password."""


class ApiError(GoalakeError):
    """The device answered with an error code."""

    def __init__(self, errcode: int, errmsg: str | None = None) -> None:
        super().__init__(f"errcode {errcode}" + (f": {errmsg}" if errmsg else ""))
        self.errcode = errcode


@dataclass(frozen=True)
class Port:
    """One physical port. `index` is the array index of the device, `label` the printed one."""

    index: int
    label: str
    is_poe: bool
    link_code: int
    admin_enabled: bool
    poe_enabled: bool | None
    power_w: float | None
    tx_kbps: int
    rx_kbps: int
    phy_mode: int | None
    flow_control: bool | None
    priority: int | None
    limit_up: int | None  # kbit/s, 0 = unlimited
    limit_down: int | None

    @property
    def connected(self) -> bool:
        return self.link_code != 0

    @property
    def speed_mbps(self) -> int:
        return LINK_SPEED.get(self.link_code, 0)


@dataclass(frozen=True)
class SwitchData:
    serial: str
    mac: str
    firmware: str
    voltage_v: float | None
    total_power_w: float | None
    temperature_c: float | None
    cloud_status: int | None
    ports: list[Port]
    settings: dict[str, Any] = field(default_factory=dict)
    netcfg: dict[str, Any] = field(default_factory=dict)
    # whole-device arrays, indexed by array index; writes send the complete array
    flow: list[int] = field(default_factory=list)
    priority: list[int] = field(default_factory=list)
    limit_up: list[int] = field(default_factory=list)
    limit_down: list[int] = field(default_factory=list)


def model_from_serial(serial: str) -> str | None:
    """Best-effort model name from the serial number, e.g. GPS208xxxxxxxx... -> GPS208."""
    match = re.match(r"^([A-Z]{2,3}\d{3}[A-Z]?)", serial or "")
    return match.group(1) if match else None


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _at(seq: Any, i: int, default: Any = None) -> Any:
    try:
        return seq[i]
    except (TypeError, IndexError, KeyError):
        return default


def port_label(index: int, poe_ports: int, total: int) -> str:
    """Map an array index to the printed port label.

    Verified on a GPS208 (web UI portIndex = [7..0], lan2list = [9, 8]): PoE port N has
    index poe_ports - N, uplinks count down from the last index as LAN1, LAN2.
    """
    if index < poe_ports:
        return str(poe_ports - index)
    return f"LAN{total - index}"


def parse_all(calldata: dict[str, Any]) -> SwitchData:
    """Turn the calldata of cmd 200 into SwitchData."""
    detail = calldata["detail"]
    link = detail.get("link") or []
    total = len(link)
    poe_ports = len(detail.get("pw") or [])
    limit = calldata.get("limit") or {}
    flow = (calldata.get("flow") or {}).get("flow")
    prio = (calldata.get("PortPri") or {}).get("PortPri")
    ports = []
    for i in range(total):
        is_poe = i < poe_ports
        pw = _num(_at(detail.get("pw"), i)) if is_poe else None
        ports.append(
            Port(
                index=i,
                label=port_label(i, poe_ports, total),
                is_poe=is_poe,
                link_code=int(_num(link[i], 0)),
                admin_enabled=bool(_at(detail.get("AdminState"), i, 1)),
                poe_enabled=bool(_at(detail.get("poec"), i)) if is_poe else None,
                power_w=pw,
                tx_kbps=int(_num(_at(detail.get("tx"), i), 0)),
                rx_kbps=int(_num(_at(detail.get("rx"), i), 0)),
                phy_mode=_at(detail.get("phyc"), i),
                flow_control=None if flow is None else bool(_at(flow, i, 0)),
                priority=_at(prio, i),
                limit_up=_at(limit.get("up"), i),
                limit_down=_at(limit.get("down"), i),
            )
        )
    tp = _num(detail.get("tp"))
    loop = calldata.get("LoopNet") or {}
    return SwitchData(
        serial=str(detail.get("sn", "")),
        mac=str(detail.get("mac", "")),
        firmware=str(detail.get("V", "")),
        voltage_v=_num(detail.get("vol")),
        total_power_w=None if tp is None else tp / 1000,  # tp is mW
        temperature_c=_num(detail.get("T")),
        cloud_status=detail.get("cloud_status"),
        ports=ports,
        settings={
            "lldp": (calldata.get("lldp") or {}).get("lldp"),
            "storm": (calldata.get("storm") or {}).get("storm"),
            "loop_detect": loop.get("LoopNet"),
            "loop_mode": loop.get("mode"),
            "watchdog": (calldata.get("AI_Wdog") or {}).get("AI_Wdog"),
            "ai_auto_extend": (calldata.get("AI_AnAuto") or {}).get("AI_AnAuto"),
            "power_warn": (calldata.get("PoWarn") or {}).get("PoWarn"),
            "dhcp_snooping": (calldata.get("dhcp_snoop") or {}).get("global_enable"),
        },
        netcfg=dict(calldata.get("netcfg") or {}),
        flow=list(flow or []),
        priority=list(prio or []),
        limit_up=list(limit.get("up") or []),
        limit_down=list(limit.get("down") or []),
    )


class GoalakeClient:
    """Client for one switch. Safe to call from several tasks, requests are serialised."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        password: str,
        *,
        port: int = 80,
        timeout: float = 10.0,
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._password = password
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._sid: str | None = None
        self._lock = asyncio.Lock()
        self._backoff = 0.0
        self._retry_at = 0.0

    def __repr__(self) -> str:  # never include the password
        return f"GoalakeClient(host={self._host!r})"

    # -- low level -------------------------------------------------------------------------

    async def _post(
        self, cmd: int, calldata: dict[str, Any] | None = None, sid: str | None = None
    ) -> tuple[dict[str, Any], str | None]:
        body: dict[str, Any] = {"callcmd": cmd}
        if calldata is not None:
            body["calldata"] = calldata
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }
        if sid:
            headers["Cookie"] = f"{sid}="
        url = f"http://{self._host}:{self._port}/{cmd}"
        started = time.monotonic()
        try:
            async with self._session.post(
                url,
                data=json.dumps({"data": body}, separators=(",", ":")),
                headers=headers,
                timeout=self._timeout,
            ) as resp:
                text = await resp.text()
                set_cookie = resp.headers.getall("Set-Cookie", [])
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            # only the type name: messages could carry request details
            _LOGGER.debug("cmd %s failed: %s", cmd, type(err).__name__)
            raise CannotConnect(f"cmd {cmd}: {type(err).__name__}") from None
        if not text:
            _LOGGER.debug("cmd %s: empty reply", cmd)
            raise CannotConnect(f"cmd {cmd}: empty reply")
        try:
            reply = json.loads(text)
        except ValueError:
            raise CannotConnect(f"cmd {cmd}: reply is not JSON") from None
        new_sid = set_cookie[0].split("=", 1)[0].strip() if set_cookie else None
        _LOGGER.debug("cmd %s ok (%d ms)", cmd, (time.monotonic() - started) * 1000)
        return reply, new_sid

    def _failed(self) -> None:
        self._backoff = min(max(self._backoff * 2, BACKOFF_START), BACKOFF_MAX)
        self._retry_at = time.monotonic() + self._backoff

    def _succeeded(self) -> None:
        self._backoff = 0.0
        self._retry_at = 0.0

    async def _login(self) -> None:
        if time.monotonic() < self._retry_at:
            raise CannotConnect("backing off after a failed login")
        self._sid = None
        try:
            reply, sid = await self._post(CMD_LOGIN, {"password": self._password})
        except CannotConnect:
            self._failed()
            raise
        data = (reply.get("data") or {}).get("calldata") or {}
        if data.get("login") == "success" and sid:
            self._sid = sid
            self._succeeded()
            _LOGGER.debug("logged in")
            return
        self._failed()
        errcode = reply.get("errcode", 0)
        if data.get("login") == "fail" or errcode in _AUTH_ERRCODES:
            raise InvalidAuth("the device rejected the password")
        raise ApiError(errcode, reply.get("errmsg"))

    async def _request(self, cmd: int, calldata: dict[str, Any] | None = None) -> dict[str, Any]:
        async with self._lock:
            if self._sid is None:
                await self._login()
            try:
                reply, _ = await self._post(cmd, calldata, self._sid)
            except CannotConnect:
                # session lost (expired, or another client logged in): log in once more
                _LOGGER.debug("session lost, logging in again")
                await self._login()
                reply, _ = await self._post(cmd, calldata, self._sid)
        errcode = reply.get("errcode", 0)
        if errcode:
            raise ApiError(errcode, reply.get("errmsg"))
        return reply

    # -- public ----------------------------------------------------------------------------

    async def check_reachable(self) -> bool:
        """True if the device answers cmd 100, which needs no login."""
        try:
            reply, _ = await self._post(CMD_STATE)
        except CannotConnect:
            return False
        return reply.get("errcode", 0) == 0

    async def is_switch(self) -> bool:
        """True if cmd 100 answers with the structure of one of these switches (no login)."""
        try:
            reply, _ = await self._post(CMD_STATE)
        except CannotConnect:
            return False
        data = (reply.get("data") or {}).get("calldata") or {}
        return reply.get("errcode", 0) == 0 and "link" in data and "AdminState" in data

    async def validate(self) -> None:
        """Log in once (config flow). Raises InvalidAuth or CannotConnect."""
        async with self._lock:
            await self._login()

    async def fetch_all(self) -> SwitchData:
        reply = await self._request(CMD_ALL)
        try:
            return parse_all(reply["data"]["calldata"])
        except (KeyError, TypeError, ValueError):
            raise ApiError(-1, "unexpected reply to cmd 200") from None

    # -- writes ----------------------------------------------------------------------------
    # Payloads follow the vendor web UI. Confirmed on a real device: nothing yet (see docs/protocol.md).

    async def _write(self, cmd: int, calldata: dict[str, Any] | None, ok_key: str) -> None:
        reply = await self._request(cmd, calldata)
        result = (reply.get("data") or {}).get("calldata") or {}
        if result.get(ok_key) != "ok":
            raise ApiError(-1, f"cmd {cmd} was not acknowledged")

    async def _port_op(self, index: int, value: int, kind: int) -> None:
        await self._write(CMD_PORT, {"opcode": value << 9 | index << 4 | kind}, "config")

    async def set_poe(self, index: int, enabled: bool) -> None:
        await self._port_op(index, 1 if enabled else 0, KIND_POE)

    async def set_port_mode(self, index: int, mode: int) -> None:
        if mode not in PORT_MODES:
            raise ValueError("invalid port mode")
        await self._port_op(index, mode, KIND_MODE)

    async def restart_port(self, index: int) -> None:
        await self._port_op(index, 1, KIND_RESTART)

    async def set_flow(self, flow: list[int]) -> None:
        await self._write(CMD_FLOW, {"flow": [1 if v else 0 for v in flow]}, "flow")

    async def set_priority(self, priority: list[int]) -> None:
        await self._write(CMD_PRIORITY, {"PortPri": [int(v) for v in priority]}, "PortPri")

    async def set_limits(self, up_kbps: list[int], down_kbps: list[int]) -> None:
        await self._write(CMD_LIMIT, {"up": list(up_kbps), "down": list(down_kbps)}, "limit")

    async def set_lldp(self, enabled: bool) -> None:
        await self._write(CMD_LLDP, {"lldp": int(enabled)}, "lldp")

    async def set_storm(self, enabled: bool) -> None:
        await self._write(CMD_STORM, {"storm": int(enabled)}, "storm")

    async def set_watchdog(self, enabled: bool) -> None:
        await self._write(CMD_WATCHDOG, {"AI_Wdog": int(enabled)}, "AI_Wdog")

    async def set_ai_auto_extend(self, enabled: bool) -> None:
        await self._write(CMD_AI_AUTO_EXTEND, {"AI_AnAuto": int(enabled)}, "AI_AnAuto")

    async def set_power_warn(self, watts: int) -> None:
        await self._write(CMD_POWER_WARN, {"PoWarn": int(watts)}, "PoWarn")

    async def reboot(self) -> None:
        """Restart the switch. Sent exactly once: the device may drop the connection while it restarts, which
        counts as success here (the session is gone either way). Never resend, a second reboot would be bad."""
        async with self._lock:
            if self._sid is None:
                await self._login()
            sid, self._sid = self._sid, None
            try:
                reply, _ = await self._post(CMD_REBOOT, None, sid)
            except CannotConnect:
                return
        if (reply.get("data") or {}).get("calldata", {}).get("reboot") != "ok":
            raise ApiError(reply.get("errcode", -1), "the reboot was not acknowledged")

    async def close(self) -> None:
        """Log out so the single session is free again. Errors are ignored: the device
        answers errcode 1003 although the session is released."""
        async with self._lock:
            sid, self._sid = self._sid, None
            if sid:
                try:
                    await self._post(CMD_LOGOUT, None, sid)
                except CannotConnect:
                    pass
