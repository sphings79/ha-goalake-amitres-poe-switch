# Device protocol notes (observed on a GPS208, firmware 6.1.260430)

Local web server (lwIP). All API calls: `POST http://<ip>/<cmd>` with JSON
`{"data": {"callcmd": <cmd>, "calldata": {...}}}`. Reply: `{"data": {"callcmd", "calldata"}, "errcode"}`.
Session: `POST /123` with `calldata: {"password": ...}`; the session cookie is a cookie whose
*name* is the session id (sent back as `Cookie: <id>=`).

Without a valid session the device closes the connection without any reply (empty response).

| cmd | Meaning | Notes |
|---|---|---|
| 100 | state | answers without login |
| 200 | all state in one reply | needs login; contains detail, netcfg, storm, vlan, PortMirror, dhcp_snoop, limit, lldp, flow, LoopNet, AI_Wdog, AI_AnAuto, PoWarn, PortPri |
| 101 | detail (sn, ip, mac, V, vol, tp, T, uplink, pw, poec, phyc, link, tx, rx, AdminState, cloud_status) | |
| 103 | PoE / duplex set, `opcode = (0x202 if on else 2) \| (port_index << 4)` | write |
| 106 / 133 / 138 | rate limit / flow control / port priority | write, from web UI source, untested |
| 107 / 115 | storm control / loop detection | |
| 108 / 109 / 114 / 118 / 124 | netcfg / VLAN / MAC table / port mirror / DHCP snooping | |
| 116 / 117 | link aggregation / spanning tree | `parameter error` without parameters |
| 129 / 130 / 131 / 140 | AI auto-extend / watchdog / cloud / PoE warning | write, untested |
| 104 / 105 / 102 / 120 / 201 | reboot / config / firmware / password / backup | never touched |

## Verified facts (vendor web UI source + probe on a GPS208 with devices on port 1 and 2)
* **Port mapping (confirmed by unplugging port 1: index 7 went to link 0 / 0 W, index 6 stayed):** array index = 8 - N for PoE port N (web UI `portIndex = [7,6,5,4,3,2,1,0]`).
  Uplinks: `LAN1` = index 9, `LAN2` = index 8. Arrays `pw` and `poec` have 8 entries (PoE ports only),
  all others have 10. The cmd 103 opcode uses the array index, not the label.
* **Link codes:** 0 off, 1/2 = 10M, 3/4 = 100M, 5 = 1000M.
* **Units:** `tp` is mW (UI shows `tp / 1000` W), `pw[i]` is W as a string, `tx`/`rx` are kbit/s (UI switches to Mb at >= 1000).
* The probe confirmed: login from a plain script works, `100`/`101`/`200` return data with a session, logout (126) sent.
* A lingering session of another client made all API calls return empty replies; after power cycling and
  removing the old integration everything worked again.

* Two-session test: with session A active, a second login (B) got an empty reply while A kept working.
  This points to one session at a time (single observation).
* `126` (logout), sent like the web UI does (no calldata), answered `errcode 1003` with empty calldata,
  so it is not confirmed that it frees the session. The web UI ignores the reply.

* Relogin test: login, logout (`errcode 1003`), login again, all succeeded at once. So logout does free the
  session despite the error code (or a new login replaces an idle one; the two-session test speaks for the first).
* One unexplained empty login reply happened between two successful probe runs; likely another client session
  (browser tab). Not verified.

## Write commands (vendor web UI source; the PoE opcode formula equals the old sscpoe integration's)
Replies acknowledge with `calldata.<key> == "ok"`. Arrays are always sent complete, indexed by array index.

| What | cmd | calldata | ack key |
|---|---|---|---|
| PoE on/off | 103 | `opcode = value << 9 \| idx << 4 \| 2` | `config` |
| Port mode (0 down, 1/2 10M h/f, 3/4 100M h/f, 5 1000M f) | 103 | `opcode = mode << 9 \| idx << 4 \| 0` | `config` |
| Restart port | 103 | `opcode = 1 << 9 \| idx << 4 \| 3` | `config` |
| Flow control | 133 | `{"flow": [10 x 0/1]}` | `flow` |
| Port priority (0 to 6) | 138 | `{"PortPri": [10 x n]}` | `PortPri` |
| Rate limit (kbit/s = Mbit/s * 1024, 0 = off) | 106 | `{"up": [10], "down": [10]}` | `limit` |
| LLDP / storm / watchdog / auto extend | 127 / 107 / 130 / 129 | `{"lldp"\|"storm"\|"AI_Wdog"\|"AI_AnAuto": 0/1}` | same key |
| Total power warning (W) | 140 | `{"PoWarn": n}` | `PoWarn` |
| Reboot | 104 | none | `reboot` |

Verified on a real GPS208 (write, read back, restore; all acknowledged with `"ok"`):
PoE on/off (103, kind 2), port mode (103, kind 0, also used by Extend), port restart (103, kind 3), flow control (133),
port priority (138), rate limits up and down (106, 51200 kbit/s = 50 Mbit/s read back as sent), LLDP (127), storm control
(107), watchdog (130), auto extend (129) and the power warning threshold (140).

Observations: PoE on/off took effect within 4 s (0 W, link 0). A port restart (kind 3) switched PoE off for about 2 s, the
device was back on PoE after about 6 s and was still negotiating its link 10 s later.

Reboot (104) was also tested: the switch was unreachable right away, answered again after about 34 s with the same firmware,
all settings kept, PoE and links back. Whether the device acknowledges `reboot` before it restarts was not recorded, so the
client sends the command once and treats a dropped connection as sent.

Not verified on a real device: everything VLAN related.
Unclear: loop detection (cmd 115 has two UI pages with different keys), how a port is administratively disabled
(`AdminState` is read only; port mode 0 = down is the candidate).

## Multicast discovery (verified on a real GPS208)
Request: UDP to 239.0.0.100:10086, text `base64(encrypt(json)) + "\r\n"` with
`{"cmd":"calludp","syn":"<8 random alphanumerics>","data":{"callcmd":"search"}}`. The encryption is a TEA variant with a 16 byte
vendor constant as key (8 byte blocks, the remaining bytes one by one); see `discovery.py`. The device answers with the same
encoding and `{"ack":"calludp","syn":...,"errcode":0,"data":{sn, ip, mac, basemodel, model, Active_state, V}}`. The reply came
back to a socket bound to the interface address (no special bind to the group needed). No password is involved.
Reachability: works from the host in the same subnet, not from a Docker/Colima container behind NAT.

## "Extend"
The old sscpoe integration calls port mode 10M (full duplex, mode 2) "Extend": the long-cable mode. Here it is the switch
`Port N extend` (on: mode 2, off: mode 5, the factory value of this device) for the PoE ports; mode 1 (10M half) is read as on.
Uplinks are left out on purpose: forcing 10M on the uplink could cut the management connection.
Verified on a real GPS208: port 1 went to `mode=10m_full` and link 10M, and back to 1000m_full with link 100M after restoring.

## Client design consequences
* Hold exactly one session, reuse it for every poll (cmd 200), send `126` on unload.
* On an empty reply: back off and re-login, never hammer the device.
* Document in the README that a parallel browser login can lock the integration out.

## Open
* Idle timeout of a session (not measured).
* Behaviour of the write commands on the real device.
