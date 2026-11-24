# Changelog

## 1.0.0

First release.

- Local control of Goalake / Amitres PoE switches (tested on a GPS208): no cloud, one reused login session, backoff when the
  switch refuses a login (it allows one session at a time).
- Setup: network search in the add dialog, discovery by multicast and DHCP, reauth, reconfigure, polling interval option,
  diagnostics with secrets redacted.
- Entities: supply voltage, total and per-port PoE power, temperature, link, speed, traffic, PoE on/off, Extend (10 Mbit/s
  long-cable mode), port mode, priority, rate limits, flow control, port restart, LLDP, storm control, watchdog, auto extend,
  power warning threshold, reboot.
- Dashboard panel in the sidebar: overview of all switches, port front view, per-port settings, switch features, seven colour
  schemes, light/dark, German and English. Changes need a Home Assistant administrator (checked on the server).
- Lovelace card `custom:goalake-poe-switch-card` with a UI editor.
- Writes are limited to the PoE ports so a mistake cannot cut the connection to the switch.
