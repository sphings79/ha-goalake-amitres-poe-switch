"""Config flow: manual setup, DHCP discovery, reauth, reconfigure and options."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from . import format_mac
from .scanner import async_scan, mac_key
from .api import CannotConnect, GoalakeClient, InvalidAuth, SwitchData, model_from_serial
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


class GoalakeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a Goalake / Amitres PoE switch."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._found: dict[str, str] = {}  # host -> label of switches found by the network scan

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> GoalakeOptionsFlow:
        return GoalakeOptionsFlow()

    def _client(self, host: str, password: str) -> GoalakeClient:
        session = async_create_clientsession(self.hass, cookie_jar=aiohttp.DummyCookieJar())
        return GoalakeClient(session, host, password)

    async def _validate(self, host: str, password: str) -> SwitchData:
        """Log in and read the state. Always logs out again: the device has one session only."""
        client = self._client(host, password)
        try:
            if not await client.is_switch():
                raise CannotConnect("not a supported switch")
            await client.validate()
            return await client.fetch_all()
        finally:
            await client.close()

    @staticmethod
    def _title(data: SwitchData) -> str:
        return f"{model_from_serial(data.serial) or 'PoE Switch'} ({format_mac(data.mac)[-4:].upper()})"

    async def _try_validate(
        self, host: str, password: str
    ) -> tuple[SwitchData | None, dict[str, str]]:
        try:
            return await self._validate(host, password), {}
        except CannotConnect:
            return None, {"base": "cannot_connect"}
        except InvalidAuth:
            return None, {"base": "invalid_auth"}
        except Exception:  # noqa: BLE001 - config flows report unknown errors to the user
            _LOGGER.exception("Unexpected error while validating the switch")
            return None, {"base": "unknown"}

    # -- manual setup ------------------------------------------------------------------------

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is None and not self._found:
            await self._scan()
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            data, errors = await self._try_validate(host, user_input[CONF_PASSWORD])
            if data is not None:
                await self.async_set_unique_id(format_mac(data.mac))
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(
                    title=self._title(data),
                    data={CONF_HOST: host, CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )
        host_field: Any = str
        if self._found:
            host_field = SelectSelector(
                SelectSelectorConfig(
                    options=[SelectOptionDict(value=h, label=label) for h, label in self._found.items()],
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): host_field,
                    vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def _scan(self) -> None:
        """Search the network and remember the switches that are not set up yet."""
        configured = {e.unique_id for e in self._async_current_entries()}
        for device in await async_scan(self.hass):
            if mac_key(str(device["mac"])) in configured or not device.get("ip"):
                continue
            self._found[device["ip"]] = f"{device.get('model') or 'PoE Switch'} ({device['ip']})"

    # -- discovery by the background scanner -------------------------------------------------

    async def async_step_integration_discovery(self, discovery_info: dict[str, Any]) -> ConfigFlowResult:
        await self.async_set_unique_id(mac_key(discovery_info["mac"]))
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info[CONF_HOST]})
        self._host = discovery_info[CONF_HOST]
        self.context["title_placeholders"] = {"host": self._host}
        return await self.async_step_discovery_confirm()

    # -- DHCP discovery ----------------------------------------------------------------------

    async def async_step_dhcp(self, discovery_info: DhcpServiceInfo) -> ConfigFlowResult:
        await self.async_set_unique_id(format_mac(discovery_info.macaddress))
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})
        # the MAC prefix belongs to the manufacturer, make sure this is such a switch
        if not await self._client(discovery_info.ip, "").is_switch():
            return self.async_abort(reason="not_supported")
        self._host = discovery_info.ip
        self.context["title_placeholders"] = {"host": discovery_info.ip}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        assert self._host is not None
        if user_input is not None:
            data, errors = await self._try_validate(self._host, user_input[CONF_PASSWORD])
            if data is not None:
                return self.async_create_entry(
                    title=self._title(data),
                    data={CONF_HOST: self._host, CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )
        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR}),
            description_placeholders={"host": self._host},
            errors=errors,
        )

    # -- reauth and reconfigure --------------------------------------------------------------

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            data, errors = await self._try_validate(entry.data[CONF_HOST], user_input[CONF_PASSWORD])
            if data is not None:
                if format_mac(data.mac) != entry.unique_id:
                    return self.async_abort(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR}),
            description_placeholders={"host": entry.data[CONF_HOST]},
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            data, errors = await self._try_validate(host, user_input[CONF_PASSWORD])
            if data is not None:
                if format_mac(data.mac) != entry.unique_id:
                    return self.async_abort(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_HOST: host, CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                    vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
                }
            ),
            errors=errors,
        )


class GoalakeOptionsFlow(OptionsFlowWithReload):
    """Options: polling interval."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])}
            )
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=1,
                            unit_of_measurement="s",
                            mode=NumberSelectorMode.BOX,
                        )
                    )
                }
            ),
        )
