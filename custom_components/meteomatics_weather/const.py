"""Constants for the Meteomatics Weather integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "meteomatics_weather"
DEFAULT_NAME = "Meteomatics"
ATTRIBUTION = "Powered by Meteomatics"

CONF_NAME = "name"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

BASE_URL = "https://api.meteomatics.com"
TIMEOUT_SECONDS = 10

DEFAULT_SCAN_INTERVAL = timedelta(minutes=10)

HOURLY_FORECAST_DAYS = 2
DAILY_FORECAST_DAYS = 7

CLOUD_COVER_PARAMETER = "effective_cloud_cover:octas"

PARAMETERS_CURRENT = [
    "t_2m:C",
    "relative_humidity_2m:p",
    "msl_pressure:hPa",
    "wind_speed_10m:ms",
    "wind_dir_10m:d",
    "precip_1h:mm",
    CLOUD_COVER_PARAMETER,
    "weather_symbol_1h:idx",
]

PARAMETERS_HOURLY = [
    "t_2m:C",
    "relative_humidity_2m:p",
    "msl_pressure:hPa",
    "wind_speed_10m:ms",
    "wind_dir_10m:d",
    "precip_1h:mm",
    CLOUD_COVER_PARAMETER,
    "weather_symbol_1h:idx",
]

PARAMETERS_DAILY = [
    "t_min_2m_24h:C",
    "t_max_2m_24h:C",
    "precip_24h:mm",
    "weather_symbol_24h:idx",
]

WEATHER_SYMBOL_MAP = {
    1: "sunny",
    2: "partlycloudy",
    3: "partlycloudy",
    4: "cloudy",
    5: "rainy",
    6: "snowy-rainy",
    7: "snowy",
    8: "rainy",
    9: "snowy",
    10: "fog",
    11: "lightning-rainy",
    12: "lightning-rainy",
    13: "pouring",
    14: "snowy",
    15: "hail",
}
