# Midea AC LAN (C3 Heat-Pump Fork)

[![Release](https://img.shields.io/github/v/release/sfortis/midea_ac_lan?include_prereleases)](https://github.com/sfortis/midea_ac_lan/releases/latest)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories/)

> **Unofficial personal fork** of [wuwentao/midea_ac_lan](https://github.com/wuwentao/midea_ac_lan).
> It tracks upstream **v0.6.12** and adds a few targeted fixes and extra entities for the
> Midea **C3 heat pump** (model `171H120F`, device protocol 3). For the full project,
> all device types, and general documentation, use the upstream repository.

This is the complete integration (the `midealocal` library is vendored, so there is **no**
`midea-local` pip dependency), plus the changes below. It keeps the `midea_ac_lan` domain,
so it drops in over the stock integration and your existing config entry, entity ids, and
history are preserved.

## What this fork changes

Full details and rationale are in **[FORK.md](FORK.md)**. In short:

- **Extra C3 entities** (opt-in via the integration's *Configure* dialog):
  - `sensor.<device_id>_room_target_temp`: the pump's room setpoint (read-only).
  - `binary_sensor.<device_id>_status_cool`: cooling-active flag, alongside the existing `status_heating`.
- **C3 ECO switch**: `switch.<device_id>_eco_mode` now raises a clear error when toggled
  in cooling (the pump only accepts ECO while heating), instead of silently snapping back to off.
- **C3 ECO parse guard**: fixes the known `IndexError` when the pump answers the ECO query with a truncated payload.
- **entity_id domain fix**: entities now build their `entity_id` from the platform domain
  (`switch.`, `sensor.`, ...) instead of the integration domain. This clears Home Assistant's
  "sets an entity ID with wrong domain" warning and avoids the entities being rejected from
  **HA 2027.5.0** onward. Existing entity ids are unchanged. (This one is a general upstream
  bug, not C3-specific.)

## Should you use this fork?

- **You have a Midea C3 heat pump** and want the extra sensors or the ECO/entity_id fixes: yes.
- **You have any other Midea appliance**: prefer [upstream](https://github.com/wuwentao/midea_ac_lan).
  This fork works for all device types (full vendor) but carries no other device-specific changes.

## Installation (HACS custom repository)

1. HACS -> three-dot menu -> **Custom repositories** -> add `https://github.com/sfortis/midea_ac_lan`, category **Integration**.
2. Search for **Midea AC LAN (sfortis heat-pump fork)** in HACS and download the latest release.
3. **Restart Home Assistant.**

Replacing the stock integration keeps the same `midea_ac_lan` domain, so devices, entity ids,
and history carry over. There is no need to re-add anything.

### Enabling the extra C3 entities

The two extra C3 entities are opt-in. After install, go to
`Settings -> Devices & Services -> Midea AC LAN -> CONFIGURE` and enable the `room_target_temp`
sensor and `status_cool` binary sensor.

## Updating

Releases are tagged `v0.6.12-hpN` (currently **`v0.6.12-hp4`**). HACS offers the newest tag;
use **Redownload** in the integration's HACS entry, then restart Home Assistant.

## Everything else

Adding devices, cloud token/key retrieval, manual configuration, refresh interval, customization,
debugging, and the full supported-appliance list are unchanged from upstream. See the upstream
docs rather than duplicating them here:

- [Upstream README](https://github.com/wuwentao/midea_ac_lan#readme)
- [Add device / configuration](https://github.com/wuwentao/midea_ac_lan#6-add-device)
- [Debug and Test](https://github.com/wuwentao/midea_ac_lan/blob/main/doc/debug.md)
- [C3 device notes](https://github.com/wuwentao/midea_ac_lan/blob/main/doc/C3.md)

> **Note:** Home Assistant 2024.4.1 or higher is required (same as upstream).

## Credits & license

All original work by the upstream authors and contributors of
[wuwentao/midea_ac_lan](https://github.com/wuwentao/midea_ac_lan) and the
[midea-local](https://github.com/midea-lan/midea-local) library. This fork only layers the
targeted C3 changes described above. Licensed under the same terms as upstream (see [LICENSE](LICENSE)).
