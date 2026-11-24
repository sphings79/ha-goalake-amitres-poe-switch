"""Registers the sidebar panel and serves its bundle."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from homeassistant.setup import async_setup_component

from .const import DOMAIN
from .websocket_api import async_register_api

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = "goalake-poe-switch"
STATIC_URL = f"/{DOMAIN}-frontend"
# custom element names are global to the page: keep them prefixed with the domain
COMPONENT_NAME = "goalake-poe-switch-panel"
BUNDLE_NAME = "goalake-poe-switch-panel.js"
CARD_BUNDLE_NAME = "goalake-poe-switch-card.js"
PANEL_TITLE = "PoE Switch"
PANEL_ICON = "mdi:switch"

DATA_STATIC_REGISTERED = "static_registered"
DATA_PANEL_REGISTERED = "panel_registered"
DATA_CARD_REGISTERED = "card_registered"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Serve the bundle and add the panel. Safe to call once per config entry."""
    data = hass.data.setdefault(DOMAIN, {})
    async_register_api(hass)

    frontend_dir = Path(__file__).parent / "frontend"
    if not (frontend_dir / BUNDLE_NAME).is_file():
        _LOGGER.warning("Panel bundle not found, the dashboard is not available")
        return
    # panel_custom (and the frontend it depends on) is not part of every setup: load it now
    if "http" not in hass.config.components or not await async_setup_component(hass, "panel_custom", {}):
        _LOGGER.debug("panel_custom or http is not available, no dashboard panel")
        return

    if not data.get(DATA_STATIC_REGISTERED):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(frontend_dir), cache_headers=False)]
        )
        data[DATA_STATIC_REGISTERED] = True

    version = str((await async_get_integration(hass, DOMAIN)).version or "dev")

    # The Lovelace card is available on every page, so it can be added to any dashboard
    if not data.get(DATA_CARD_REGISTERED) and (frontend_dir / CARD_BUNDLE_NAME).is_file():
        frontend.add_extra_js_url(hass, f"{STATIC_URL}/{CARD_BUNDLE_NAME}?v={version}")
        data[DATA_CARD_REGISTERED] = True

    if data.get(DATA_PANEL_REGISTERED):
        return
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=COMPONENT_NAME,
        module_url=f"{STATIC_URL}/{BUNDLE_NAME}?v={version}",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=False,
    )
    data[DATA_PANEL_REGISTERED] = True


def async_remove_panel_if_unused(hass: HomeAssistant) -> None:
    """Take the panel out of the sidebar when the last switch is unloaded."""
    data = hass.data.get(DOMAIN, {})
    if not data.get(DATA_PANEL_REGISTERED) or hass.config_entries.async_loaded_entries(DOMAIN):
        return
    frontend.async_remove_panel(hass, PANEL_URL_PATH)
    data[DATA_PANEL_REGISTERED] = False
