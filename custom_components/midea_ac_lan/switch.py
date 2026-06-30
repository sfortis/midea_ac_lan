"""Switch for Midea Lan."""

from typing import Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_SWITCHES, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from midealocal.device import DeviceType
from midealocal.devices.c3 import DeviceAttributes as C3Attributes
from midealocal.devices.c3.const import C3DeviceMode

from .const import DEVICES, DOMAIN
from .midea_devices import MIDEA_DEVICES
from .midea_entity import MideaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches for device."""
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES].get(device_id)
    extra_switches = config_entry.options.get(CONF_SWITCHES, [])
    switches = []
    for entity_key, config in cast(
        "dict",
        MIDEA_DEVICES[device.device_type]["entities"],
    ).items():
        if config["type"] == Platform.SWITCH and entity_key in extra_switches:
            if (
                device.device_type == DeviceType.C3
                and entity_key == C3Attributes.eco_mode
            ):
                dev = MideaC3EcoSwitch(device, entity_key)
            else:
                dev = MideaSwitch(device, entity_key)
            switches.append(dev)
    async_add_entities(switches)


class MideaSwitch(MideaEntity, ToggleEntity):
    """Represent a Midea switch."""

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return cast("bool", self._device.get_attribute(self._entity_key))

    def turn_on(self, **kwargs: Any) -> None:  # noqa: ANN401, ARG002
        """Turn on switch."""
        self._device.set_attribute(attr=self._entity_key, value=True)

    def turn_off(self, **kwargs: Any) -> None:  # noqa: ANN401, ARG002
        """Turn off switch."""
        self._device.set_attribute(attr=self._entity_key, value=False)


class MideaC3EcoSwitch(MideaSwitch):
    """C3 ECO switch.

    The C3 heat pump only accepts ECO mode while heating; in cooling it
    silently refuses the command and the switch snaps back to off. Block the
    request up front with a clear error instead of letting it fail silently.
    """

    def turn_on(self, **kwargs: Any) -> None:  # noqa: ANN401, ARG002
        """Turn on ECO mode, but only while the pump is in heating mode.

        Raises
        ------
        HomeAssistantError
            If the pump is not in heating mode, where ECO is not available.

        """
        if self._device.get_attribute(C3Attributes.mode) != C3DeviceMode.HEAT:
            raise HomeAssistantError(
                "ECO mode can only be enabled while the heat pump is in heating "
                "mode",
            )
        self._device.set_attribute(attr=self._entity_key, value=True)
