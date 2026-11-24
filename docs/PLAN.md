# Project plan

Domain `goalake_poe_switch`, MIT, Home Assistant >= 2025.9, local HTTP API only, no cloud,
no extra Python dependencies. Public repo, HACS (default store) compliant.

## Phases
0. Scaffold, mock switch (`dev-sim/`), protocol notes, clarify session behaviour of the device.
1. API client: login, session reuse and re-login, one request per interval (cmd 200).
   Passwords, session ids and MACs must never reach the log (tested).
2. Config flow: manual, DHCP discovery (MAC prefix 5C15C5), multicast discovery, reauth,
   reconfigure, options, diagnostics with redaction. Multiple devices = multiple entries.
3. Entities: sensors, per-port PoE/admin/duplex/flow/QoS/rate limit, watchdog, AI auto-extend,
   PoE warning threshold, storm, loop detect, LLDP, reboot button. Diagnostics disabled by default.
4. Sidebar dashboard panel (Lit/TypeScript/Vite, bundle committed): overview, device detail with
   port front view, port config, settings. All palettes of the Marstek Modbus Suite, de/en.
   Write access admin-only, checked server side.
5. Lovelace card (status + optional PoE switching, configurable in the card editor).
6. VLAN editor (admin only, strong warning, management port protected). Last, tested on a spare switch.
7. Release: tests, README (de/en), screenshots, HACS checks, repo public.

## Out of scope
Cloud access, firmware update, password change, config backup, schedules.
