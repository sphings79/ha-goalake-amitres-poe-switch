"""Mock Goalake/Amitres PoE switch for development and tests.

Mimics the observed behaviour of the real device:
  * cmd 100 answers without login, every other cmd needs the session cookie
  * a request without a valid session gets NO reply (connection is closed)
  * POST /<cmd> with JSON body {"data": {"callcmd": cmd, "calldata": {...}}}

Usage: python3 dev-sim/mock_switch.py [--host 127.0.0.1] [--port 8080] [--password test1234]
                                       [--fail-mode none|empty|expire]
"""

from __future__ import annotations

import argparse
import copy
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "gps208.json"
COOKIE_NAME = "sim"


class State:
    def __init__(self, password: str, fail_mode: str) -> None:
        self.password = password
        self.fail_mode = fail_mode
        self.data = json.loads(FIXTURE.read_text())
        self.sessions: set[str] = set()
        self.requests = 0
        self.logins = 0
        self.reboot_drops = False  # real device behaviour is not known: test both
        self.reboots = 0


def build_all(st: State) -> dict:
    return copy.deepcopy(st.data)


def reply(cmd: int, calldata: dict, errcode: int = 0, errmsg: str | None = None) -> dict:
    out: dict = {"data": {"callcmd": cmd, "calldata": calldata}, "errcode": errcode}
    if errmsg:
        out["errmsg"] = errmsg
    return out


def handle(st: State, cmd: int, calldata: dict | None) -> dict:
    d = st.data
    det = d["detail"]
    if cmd == 100:
        return reply(100, {
            "pw": det["pw"], "link": det["link"], "AdminState": det["AdminState"],
            "Active_state": "active", "uplink": det["uplink"],
        })
    if cmd == 101:
        return reply(101, det)
    if cmd == 200:
        return reply(200, build_all(st))
    getters = {106: "limit", 107: "storm", 108: "netcfg", 109: "vlan", 115: "LoopNet",
               118: "PortMirror", 124: "dhcp_snoop"}
    if cmd in getters and not calldata:
        return reply(cmd, d[getters[cmd]])
    if cmd in (114, 136):
        return reply(cmd, {})
    if cmd == 137:
        return reply(cmd, {"sn": []})
    if cmd in (116, 117):
        return reply(cmd, {}, -1, "parameter error")
    if cmd == 103 and calldata:
        opcode = int(calldata.get("opcode", 0))
        kind, index, value = opcode & 0xF, (opcode >> 4) & 0x1F, opcode >> 9
        if kind == 2 and index < len(det["poec"]):
            det["poec"][index] = value
            if not value and index < len(det["pw"]):
                det["pw"][index] = "0"
        elif kind == 0 and index < len(det["phyc"]):
            det["phyc"][index] = value
        return reply(103, {"config": "ok"})
    if calldata:
        # every write stores {key: value} under the same key it acknowledges with
        writes = {107: "storm", 127: "lldp", 129: "AI_AnAuto", 130: "AI_Wdog",
                  133: "flow", 138: "PortPri", 140: "PoWarn"}
        if cmd in writes:
            key = writes[cmd]
            d[key] = {key: calldata[key]}
            return reply(cmd, {key: "ok"})
        if cmd == 106:
            d["limit"] = {"up": calldata["up"], "down": calldata["down"]}
            return reply(106, {"limit": "ok"})
    if cmd == 104:
        st.reboots += 1
        return reply(104, {"reboot": "ok"})
    return reply(cmd, {}, -1, "parameter error")


def make_handler(st: State):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, fmt, *args):  # never log bodies or cookies
            print(f"{self.command} {self.path.split('?')[0]}")

        def _send_json(self, obj: dict, extra: dict | None = None) -> None:
            raw = json.dumps(obj, separators=(",", ":")).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _drop(self) -> None:
            self.close_connection = True
            self.connection.close()

        def do_GET(self):
            body = b"<html><title>Cloud Switch (simulator)</title></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            st.requests += 1
            length = int(self.headers.get("Content-Length", 0))
            try:
                req = json.loads(self.rfile.read(length) or b"{}")["data"]
                cmd = int(req["callcmd"])
            except Exception:
                return self._drop()
            calldata = req.get("calldata")
            if st.fail_mode == "empty":
                return self._drop()
            if cmd == 123:
                if calldata and calldata.get("password") == st.password:
                    sid = secrets.token_hex(8)
                    st.sessions.add(sid)
                    st.logins += 1
                    return self._send_json(
                        reply(123, {"login": "success"}),
                        {"Set-Cookie": f"{COOKIE_NAME}{sid}=; Path=/"},
                    )
                return self._send_json(reply(123, {"login": "fail"}, 1009))
            if cmd != 100:
                cookie = self.headers.get("Cookie", "")
                sid = cookie.split("=")[0].removeprefix(COOKIE_NAME).strip()
                if sid not in st.sessions:
                    return self._drop()
                if cmd == 126:
                    st.sessions.discard(sid)
                    return self._send_json(reply(126, {"logout": "success"}))
                if st.fail_mode == "expire" and st.requests % 5 == 0:
                    st.sessions.discard(sid)
                    return self._drop()
            if cmd == 104 and st.reboot_drops:
                st.reboots += 1
                st.sessions.clear()
                return self._drop()
            self._send_json(handle(st, cmd, calldata))

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--password", default="test1234")
    ap.add_argument("--fail-mode", choices=["none", "empty", "expire"], default="none")
    a = ap.parse_args()
    st = State(a.password, a.fail_mode)
    srv = ThreadingHTTPServer((a.host, a.port), make_handler(st))
    print(f"mock switch on http://{a.host}:{a.port} fail-mode={a.fail_mode}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
