# Targeted C3 Heat-Pump Fork

Personal fork of [wuwentao/midea_ac_lan](https://github.com/wuwentao/midea_ac_lan) (based on upstream **0.6.12**) that exposes two extra entities for the Midea **C3 heat pump** (model 171H120F, device protocol 3), which the stock integration parses internally but never surfaces.

## What this fork adds

| Entity | Type | Notes |
|--------|------|-------|
| `sensor.<device_id>_room_target_temp` | sensor (temperature, C) | The pump's room setpoint. Already a climate attribute upstream, here promoted to its own sensor. Readable, not settable. Comes from the **X01** frame, polled every `refresh_interval` (30s). |
| `binary_sensor.<device_id>_status_cool` | binary_sensor (running) | Cooling-active flag. Parsed by `C3EnergyBody` upstream but never stored in `DeviceAttributes`. Comes from the **X04** notify push (sparse, state-change driven), same path as `status_heating`. |

## How it is built (the 5 changes)

The hard requirement is that the integration must run **without** the pip `midea-local` dependency, so the library is vendored.

1. **Vendored `midealocal`** (full copy of v6.8.0) into `custom_components/midea_ac_lan/midealocal/`.
   - `custom_components/midea_ac_lan/__init__.py` does `sys.path.insert(0, os.path.dirname(__file__))` before any `from midealocal ...` import, so the bundled copy wins. No import rewrite needed.
   - `manifest.json` has `"requirements": []` (no pip dep).
   - NOTE: a slim "only c3" vendor was tried first and failed: `midea_devices.py` imports `DeviceAttributes` from **every** device type, so the full device tree must be present. Keep all of `midealocal/devices/`.

2. **status_cool patch** (2 lines) in the vendored C3:
   - `midealocal/devices/c3/const.py`: add `status_cool = "status_cool"` to the `DeviceAttributes` enum.
   - `midealocal/devices/c3/__init__.py`: add `DeviceAttributes.status_cool: None` to the `attributes` init dict.
   - That is all: `process_message` is generic (iterates `_attributes` and copies any matching message field via `hasattr`), and `C3EnergyBody` already parses `status_cool` (`status_byte & 0x02`).

3. **ECO switch behaviour** - two small, independent changes:
   - Context: the ECO switch (`switch.<device_id>_eco_mode`) appeared to "reject" turning on. This is **correct hardware behaviour**: the C3 only accepts ECO while heating; in cooling it silently refuses and the switch snaps back to off (verified against the official Midea app). `eco_mode` is read from the **X01** basic frame (`C3BasicBody`, `body[+2] & 0x08`) and that read is fine - left unchanged.
   - Vendored `midealocal/devices/c3/message.py`: in `C3ECOBody` the `eco_function_state` / `eco_timer_state` parse is wrapped in a `len(body) > data_offset` guard, killing the known C3 ECO `IndexError` when the pump answers the X07 ECO query (or echoes a set) with a truncated body.
   - Wrapper `switch.py` (not vendored): a `MideaC3EcoSwitch(MideaSwitch)` subclass is used for the C3 `eco_mode` switch. Its `turn_on` raises `HomeAssistantError` ("ECO mode can only be enabled while the heat pump is in heating mode") when `C3Attributes.mode != C3DeviceMode.HEAT`, so a cool-mode toggle gives a clear notification instead of a silent revert.

4. **Entity definitions** in `midea_devices.py` (C3 block, `0xC3`):
   - `C3Attributes.status_cool` -> `Platform.BINARY_SENSOR` (running, mdi:snowflake)
   - `C3Attributes.room_target_temp` -> `Platform.SENSOR` (temperature, C, mdi:home-thermometer)
   - Plus `translation_key` entries in `translations/en.json`.

5. **hacs.json**: removed `zip_release`/`filename` so HACS downloads the source directly (no zip asset to maintain).

## Installation (HACS custom repository)

1. HACS -> three-dot menu -> Custom repositories -> add `https://github.com/sfortis/midea_ac_lan`, category Integration.
2. Download the latest release (e.g. `v0.6.12-hp1`).
3. Restart Home Assistant.
4. The two new sensors are opt-in: enable them via the integration's **Configure** dialog (they are added to `config_entry.options.sensors`).

Domain stays `midea_ac_lan`, so an existing config entry, entity ids, unique ids and history are preserved when replacing the stock integration.

## What is NOT possible on this hardware (verified)

- **Water inlet/outlet temps, compressor frequency, voltage, EXV current** (`temp_tw_in`/`temp_tw_out`, X10 `C3UnitParaBody`): the pump **times out** on the X10 query (and X09 Disinfect), so the integration marks them unsupported and skips. These attributes stay `None`. A Modbus adapter on the pump is the only way to get them.
- **Active X04 polling** (to refresh status/energy faster than the sparse push): tested by adding a `MessageQueryEnergy` (X04) to `build_query`. The pump **answers** the X04 query (no timeout) but returns an **empty** payload (`aa12c3...0000000000000024`), which only causes a parse error. Real status/energy come **only** via notify push. Reverted; do not re-add.
- **DHW, backup heaters (TBH/IBH), tank temp**: not physically present on this install. The related flags (`status_dhw`, `status_tbh`, `status_ibh`, `tank_actual_temperature`, `fast_dhw`) are fake/unused. Ignore them.
- **ECO mode in cooling**: the pump only accepts ECO while heating (confirmed in the official app). A cool-mode ECO request is refused by the hardware; the integration now blocks it up front with a clear error (see change 3). This is not a bug.

## Maintainability

On an upstream `midea-local` update you want to pick up:
1. Re-vendor `midealocal/` (copy from the new pip version / upstream).
2. Re-apply the 2-line `status_cool` patch (const.py + c3 `__init__.py`).
3. Re-apply the `C3ECOBody` `len(body) > data_offset` guard in c3 `message.py` (the ECO `IndexError` fix) - unless upstream has fixed it by then.
4. Keep the `midea_devices.py` entity entries + `MideaC3EcoSwitch` heat-only guard in `switch.py` + `__init__.py` sys.path + `manifest.json` requirements changes (these live in wrapper files, not the vendored lib).
5. Bump version in `manifest.json`, create a new release tag, HACS will offer the update.

Ideally, the `status_cool` gap is worth a PR upstream (the lib parses it but never exposes it), which would remove the need to patch the vendored copy.

## Upstream tracking

Base: integration `wuwentao/midea_ac_lan` **v0.6.12** + library `midea-local` (`midea-lan/midea-local`, formerly rokam) **6.8.0**.

Checked **2026-06-26**:
- Integration v0.6.12 is the latest release; no C3 wrapper commits after it.
- Library v6.9.0 (2026-06-25) released, but **no C3 changes**: features are `ac` (B5 per-mode min/max temps) and `e2` (water heater memo / heating-power multiplier); one general bug fix (`asyncio.Lock` instead of `threading.Lock`, #482, connection robustness for all devices). The C3 ECO `IndexError` is NOT fixed and `status_cool` was NOT added upstream, so this fork stays necessary.

Re-vendor only when a release ships a real C3 fix (e.g. the ECO parse error, or upstream finally exposing `status_cool`). v6.9.0 alone is not worth a re-vendor.
