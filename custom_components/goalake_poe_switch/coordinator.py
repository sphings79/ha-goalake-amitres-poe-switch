"""Data update coordinator: one request (cmd 200) per interval over one session."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, CannotConnect, GoalakeClient, InvalidAuth, SwitchData
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GoalakeCoordinator(DataUpdateCoordinator[SwitchData]):
    """Polls one switch."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: GoalakeClient) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.entry_id}",
            update_interval=timedelta(seconds=interval),
        )
        self.client = client

    async def _async_update_data(self) -> SwitchData:
        try:
            return await self.client.fetch_all()
        except InvalidAuth as err:
            raise ConfigEntryAuthFailed("the switch rejected the password") from err
        except CannotConnect as err:
            # shown to the user, translated (see "exceptions" in translations)
            raise UpdateFailed(translation_domain=DOMAIN, translation_key="cannot_connect") from err
        except ApiError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="api_error",
                translation_placeholders={"error": str(err)},
            ) from err
