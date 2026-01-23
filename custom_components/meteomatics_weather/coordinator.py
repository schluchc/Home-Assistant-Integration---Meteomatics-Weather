"""Data coordinator for Meteomatics Weather."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    BASE_URL,
    CONF_PASSWORD,
    CONF_USERNAME,
    CLOUD_COVER_PARAMETER,
    DAILY_FORECAST_DAYS,
    DEFAULT_SCAN_INTERVAL,
    HOURLY_FORECAST_DAYS,
    PARAMETERS_CURRENT,
    PARAMETERS_DAILY,
    PARAMETERS_HOURLY,
    TIMEOUT_SECONDS,
    WEATHER_SYMBOL_MAP,
)

_LOGGER = logging.getLogger(__name__)


async def async_fetch_meteomatics(
    hass: HomeAssistant,
    username: str,
    password: str,
    lat: float,
    lon: float,
    time_range: str,
    parameters: list[str],
) -> dict[str, Any]:
    """Fetch Meteomatics data for a time range and parameter list."""
    url = f"{BASE_URL}/{time_range}/{','.join(parameters)}/{lat},{lon}/json"
    session = async_get_clientsession(hass)
    auth = aiohttp.BasicAuth(username, password)

    try:
        async with session.get(url, auth=auth, timeout=TIMEOUT_SECONDS) as resp:
            if resp.status in (401, 403):
                raise ConfigEntryAuthFailed("Invalid authentication")
            if resp.status >= 400:
                body = await resp.text()
                _LOGGER.error(
                    "Meteomatics API error %s on %s: %s",
                    resp.status,
                    url,
                    body[:500],
                )
                resp.raise_for_status()
            return await resp.json()
    except aiohttp.ClientResponseError as err:
        if err.status in (401, 403):
            raise ConfigEntryAuthFailed("Invalid authentication") from err
        raise


async def async_test_connection(
    hass: HomeAssistant, username: str, password: str
) -> None:
    """Check credentials by requesting a single data point."""
    await async_fetch_meteomatics(
        hass,
        username,
        password,
        hass.config.latitude,
        hass.config.longitude,
        _format_time(dt_util.utcnow()),
        ["t_2m:C"],
    )


class MeteomaticsDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage Meteomatics data updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._username = entry.data[CONF_USERNAME]
        self._password = entry.data[CONF_PASSWORD]
        self._lat = hass.config.latitude
        self._lon = hass.config.longitude

        super().__init__(
            hass,
            _LOGGER,
            name="meteomatics_weather",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        now = dt_util.utcnow()
        hourly_end = now + timedelta(days=HOURLY_FORECAST_DAYS)
        daily_end = now + timedelta(days=DAILY_FORECAST_DAYS)

        hourly_range = f"{_format_time(now)}--{_format_time(hourly_end)}:PT1H"
        daily_range = f"{_format_time(now)}--{_format_time(daily_end)}:P1D"

        try:
            current_task = async_fetch_meteomatics(
                self.hass,
                self._username,
                self._password,
                self._lat,
                self._lon,
                _format_time(now),
                PARAMETERS_CURRENT,
            )
            hourly_task = async_fetch_meteomatics(
                self.hass,
                self._username,
                self._password,
                self._lat,
                self._lon,
                hourly_range,
                PARAMETERS_HOURLY,
            )
            daily_task = async_fetch_meteomatics(
                self.hass,
                self._username,
                self._password,
                self._lat,
                self._lon,
                daily_range,
                PARAMETERS_DAILY,
            )

            current_payload, hourly_payload, daily_payload = await asyncio.gather(
                current_task, hourly_task, daily_task
            )
        except ConfigEntryAuthFailed:
            raise
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(f"Meteomatics API error: {err.status}") from err
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed("Error communicating with Meteomatics") from err

        current_map = _extract_parameter_map(current_payload)
        hourly_map = _extract_parameter_map(hourly_payload)
        daily_map = _extract_parameter_map(daily_payload)

        return {
            "current": _build_current(current_map),
            "hourly": _build_hourly_forecast(hourly_map),
            "daily": _build_daily_forecast(daily_map),
        }


def _extract_parameter_map(
    payload: dict[str, Any]
) -> dict[str, dict[datetime, float | None]]:
    result: dict[str, dict[datetime, float | None]] = {}
    for entry in payload.get("data", []):
        param = entry.get("parameter")
        coords = entry.get("coordinates") or []
        if not param or not coords:
            continue
        dates = coords[0].get("dates") or []
        series: dict[datetime, float | None] = {}
        for item in dates:
            raw_date = item.get("date")
            if not raw_date:
                continue
            parsed = dt_util.parse_datetime(raw_date)
            if parsed is None:
                continue
            series[dt_util.as_utc(parsed)] = _as_float(item.get("value"))
        if series:
            result[param] = series
    return result


def _format_time(value: datetime) -> str:
    utc_value = dt_util.as_utc(value)
    return utc_value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _octas_to_percent(value: float | None) -> float | None:
    if value is None:
        return None
    percent = (value / 8.0) * 100.0
    return max(0.0, min(100.0, percent))


def _first_value(series_map: dict[str, dict[datetime, float | None]], key: str) -> float | None:
    series = series_map.get(key)
    if not series:
        return None
    first_time = sorted(series)[0]
    return series[first_time]


def _value_at(
    series_map: dict[str, dict[datetime, float | None]],
    key: str,
    when: datetime,
) -> float | None:
    series = series_map.get(key)
    if not series:
        return None
    return series.get(when)


def _select_times(
    series_map: dict[str, dict[datetime, float | None]],
    preferred_keys: list[str],
) -> list[datetime]:
    for key in preferred_keys:
        if key in series_map:
            return sorted(series_map[key])
    if not series_map:
        return []
    first_series = next(iter(series_map.values()))
    return sorted(first_series)


def _map_condition(code: float | None) -> str | None:
    if code is None:
        return None
    try:
        code_int = int(code)
    except (TypeError, ValueError):
        return None
    if code_int >= 100:
        night_code = code_int - 100
        mapped = WEATHER_SYMBOL_MAP.get(night_code)
        if mapped == "sunny":
            return "clear-night"
        return mapped
    return WEATHER_SYMBOL_MAP.get(code_int)


def _build_current(series_map: dict[str, dict[datetime, float | None]]) -> dict[str, Any]:
    return {
        "temperature": _first_value(series_map, "t_2m:C"),
        "humidity": _first_value(series_map, "relative_humidity_2m:p"),
        "pressure": _first_value(series_map, "msl_pressure:hPa"),
        "wind_speed": _first_value(series_map, "wind_speed_10m:ms"),
        "wind_bearing": _first_value(series_map, "wind_dir_10m:d"),
        "precipitation": _first_value(series_map, "precip_1h:mm"),
        "cloud_coverage": _octas_to_percent(
            _first_value(series_map, CLOUD_COVER_PARAMETER)
        ),
        "condition": _map_condition(_first_value(series_map, "weather_symbol_1h:idx")),
    }


def _build_hourly_forecast(
    series_map: dict[str, dict[datetime, float | None]]
) -> list[dict[str, Any]]:
    times = _select_times(series_map, ["t_2m:C", "weather_symbol_1h:idx"])
    forecast: list[dict[str, Any]] = []
    for when in times:
        entry: dict[str, Any] = {"datetime": when}
        temperature = _value_at(series_map, "t_2m:C", when)
        if temperature is not None:
            entry["temperature"] = temperature
        condition = _map_condition(_value_at(series_map, "weather_symbol_1h:idx", when))
        if condition:
            entry["condition"] = condition
        precipitation = _value_at(series_map, "precip_1h:mm", when)
        if precipitation is not None:
            entry["precipitation"] = precipitation
        wind_speed = _value_at(series_map, "wind_speed_10m:ms", when)
        if wind_speed is not None:
            entry["wind_speed"] = wind_speed
        wind_bearing = _value_at(series_map, "wind_dir_10m:d", when)
        if wind_bearing is not None:
            entry["wind_bearing"] = wind_bearing
        humidity = _value_at(series_map, "relative_humidity_2m:p", when)
        if humidity is not None:
            entry["humidity"] = humidity
        pressure = _value_at(series_map, "msl_pressure:hPa", when)
        if pressure is not None:
            entry["pressure"] = pressure
        cloud_coverage = _octas_to_percent(
            _value_at(series_map, CLOUD_COVER_PARAMETER, when)
        )
        if cloud_coverage is not None:
            entry["cloud_coverage"] = cloud_coverage
        forecast.append(entry)
    return forecast


def _build_daily_forecast(
    series_map: dict[str, dict[datetime, float | None]]
) -> list[dict[str, Any]]:
    times = _select_times(series_map, ["t_max_2m_24h:C", "t_min_2m_24h:C"])
    forecast: list[dict[str, Any]] = []
    for when in times:
        entry: dict[str, Any] = {"datetime": when}
        temp_max = _value_at(series_map, "t_max_2m_24h:C", when)
        if temp_max is not None:
            entry["temperature"] = temp_max
        temp_min = _value_at(series_map, "t_min_2m_24h:C", when)
        if temp_min is not None:
            entry["temperature_low"] = temp_min
        condition = _map_condition(_value_at(series_map, "weather_symbol_24h:idx", when))
        if condition:
            entry["condition"] = condition
        precipitation = _value_at(series_map, "precip_24h:mm", when)
        if precipitation is not None:
            entry["precipitation"] = precipitation
        forecast.append(entry)
    return forecast
