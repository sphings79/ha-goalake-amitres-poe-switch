"""Read-only probe for a real switch. Run it yourself; the password comes from the environment.

    GOALAKE_PASSWORD='...' python3 -I dev-sim/probe.py <ip> [port] [--two-sessions | --relogin]

Logs in, reads cmd 100, 101 and 200, logs out (cmd 126, frees the single session) and prints
the result as JSON. The password is never printed; session id, serial number and MAC are redacted.
"""

from __future__ import annotations

import http.client
import json
import os
import sys

REDACT = {"sn", "mac"}


def redact(obj):
    if isinstance(obj, dict):
        return {k: ("<redacted>" if k in REDACT else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


def call(ip: str, port: int, cmd: int, calldata=None, sid: str | None = None):
    body = {"callcmd": cmd}
    if calldata is not None:
        body["calldata"] = calldata
    raw = json.dumps({"data": body}, separators=(",", ":"))
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": f"http://{ip}",
        "Referer": f"http://{ip}/",
    }
    if sid:
        headers["Cookie"] = f"{sid}="
    conn = http.client.HTTPConnection(ip, port, timeout=10)
    try:
        conn.request("POST", f"/{cmd}", raw, headers)
        resp = conn.getresponse()
        text = resp.read().decode("utf-8", "replace")
        new_sid = None
        for name, value in resp.getheaders():
            if name.lower() == "set-cookie":
                new_sid = value.split("=", 1)[0].strip()
        return resp.status, text, new_sid
    finally:
        conn.close()


def two_sessions(ip: str, port: int, password: str) -> int:
    """Open two sessions and check whether the first one survives the second login."""
    result: dict = {}
    sids: dict[str, str | None] = {}
    try:
        for name in ("A", "B"):
            try:
                _, text, sid = call(ip, port, 123, {"password": password})
                sids[name] = sid
                result[f"login_{name}"] = bool(sid) and '"login":"success"' in text
            except Exception as exc:
                sids[name] = None
                result[f"login_{name}"] = f"ERROR {type(exc).__name__}"
        steps = [("A", 200), ("B", 200), ("A", 200)]
        for i, (name, cmd) in enumerate(steps, 1):
            try:
                _, text, _ = call(ip, port, cmd, sid=sids.get(name))
                result[f"step{i}_{name}_cmd{cmd}"] = "ok" if '"errcode":0' in text else (text[:80] or "EMPTY REPLY")
            except Exception as exc:
                result[f"step{i}_{name}_cmd{cmd}"] = f"ERROR {type(exc).__name__}"
    finally:
        for name, sid in sids.items():
            if sid:
                try:
                    _, text, _ = call(ip, port, 126, sid=sid)
                    result[f"logout_{name}"] = text[:100] or "EMPTY REPLY"
                except Exception as exc:
                    result[f"logout_{name}"] = f"ERROR {type(exc).__name__}"
    print(json.dumps(result, indent=1))
    return 0


def relogin(ip: str, port: int, password: str) -> int:
    """Login, logout, then login again at once: does logout (126) really free the session?"""
    result: dict = {}
    for n in (1, 2):
        sid = None
        try:
            _, text, sid = call(ip, port, 123, {"password": password})
            result[f"login_{n}"] = bool(sid) and '"login":"success"' in text
        except Exception as exc:
            result[f"login_{n}"] = f"ERROR {type(exc).__name__}"
        if sid:
            try:
                _, text, _ = call(ip, port, 126, sid=sid)
                result[f"logout_{n}"] = text[:100] or "EMPTY REPLY"
            except Exception as exc:
                result[f"logout_{n}"] = f"ERROR {type(exc).__name__}"
    print(json.dumps(result, indent=1))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    two = "--two-sessions" in sys.argv
    again = "--relogin" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ip = args[0]
    port = int(args[1]) if len(args) > 1 else 80
    password = os.environ.get("GOALAKE_PASSWORD")
    if not password:
        print("GOALAKE_PASSWORD is not set")
        return 2

    if two:
        return two_sessions(ip, port, password)
    if again:
        return relogin(ip, port, password)
    result: dict = {}
    sid = None
    try:
        status, text, sid = call(ip, port, 123, {"password": password})
        login_ok = '"login":"success"' in text
        result["login"] = {"http": status, "ok": login_ok, "session_cookie": bool(sid)}
        if login_ok and sid:
            for cmd in (100, 101, 200):
                try:
                    status, text, _ = call(ip, port, cmd, sid=sid)
                    result[str(cmd)] = redact(json.loads(text)) if text else "EMPTY REPLY"
                except Exception as exc:  # never include request data in messages
                    result[str(cmd)] = f"ERROR {type(exc).__name__}"
    except Exception as exc:
        result["login"] = f"ERROR {type(exc).__name__}"
    finally:
        if sid:
            try:
                _, text, _ = call(ip, port, 126, sid=sid)
                result["logout"] = text[:100] or "EMPTY REPLY"
            except Exception as exc:
                result["logout"] = f"ERROR {type(exc).__name__}"
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
