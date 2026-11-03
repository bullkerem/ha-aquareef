"""Config flow for AquaReef Aquarium Lighting integration."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import aiohttp
from aiohttp import BasicAuth
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_HOST,
    CONF_HTTP_PORT,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    DEFAULT_HTTP_PORT,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class AquaReefConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AquaReef."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            http_port = user_input.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT)
            username = user_input.get(CONF_USERNAME, DEFAULT_USERNAME)
            password = user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD)
            name = user_input.get(CONF_NAME, DEFAULT_NAME).strip()

            mac: str | None = None

            # Test connection
            try:
                # 1. Probe HTTP status
                url = f"http://{host}:{http_port}/status_en.html"
                auth = BasicAuth(username, password)
                timeout = aiohttp.ClientTimeout(total=3)
                async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            match = re.search(r'cover_sta_mac\s*=\s*"([^"]*)";', text)
                            if match:
                                mac = match.group(1).upper()
            except Exception as err:
                _LOGGER.debug("HTTP check during setup failed: %s", err)

            # 2. Test TCP socket if HTTP didn't catch MAC
            if not mac:
                try:
                    _, writer = await asyncio.wait_for(
                        asyncio.open_connection(host, port),
                        timeout=2.0,
                    )
                    writer.close()
                    await writer.wait_closed()
                except Exception as err:
                    _LOGGER.warning("TCP check to AquaReef %s:%s failed: %s", host, port, err)
                    errors["base"] = "cannot_connect"

            if not errors:
                unique_id = mac or f"aquareef_{host}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_HTTP_PORT: http_port,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_NAME: name,
                        "mac": unique_id,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.8.90"): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_HTTP_PORT, default=DEFAULT_HTTP_PORT): int,
                vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
                vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
