"""Config flow for Meteomatics Weather."""
from __future__ import annotations

import asyncio
import logging

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.typing import ConfigType

from .const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME, DEFAULT_NAME, DOMAIN
from .coordinator import async_test_connection

_LOGGER = logging.getLogger(__name__)


class MeteomaticsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meteomatics Weather."""

    VERSION = 1

    async def async_step_user(self, user_input: ConfigType | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._async_validate(user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def _async_validate(self, data: ConfigType) -> dict[str, str]:
        errors: dict[str, str] = {}

        try:
            await async_test_connection(
                self.hass, data[CONF_USERNAME], data[CONF_PASSWORD]
            )
        except ConfigEntryAuthFailed:
            errors["base"] = "invalid_auth"
        except (aiohttp.ClientError, asyncio.TimeoutError):
            errors["base"] = "cannot_connect"
        except Exception:  # pragma: no cover - safety net
            _LOGGER.exception("Unexpected error while validating Meteomatics")
            errors["base"] = "unknown"

        return errors
