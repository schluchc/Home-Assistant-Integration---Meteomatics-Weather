# Meteomatics Weather

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/grhawk/Home-Assistant-Integration---Meteomatics-Weather)
![License](https://img.shields.io/github/license/grhawk/Home-Assistant-Integration---Meteomatics-Weather)

Custom Home Assistant integration for Meteomatics weather data (current, hourly, daily).

## Table of contents
- Features
- Screenshots
- Install with HACS (custom repo)
- Manual install
- Configure
- Supported parameters
- Services and attributes
- Troubleshooting
- Notes

## Features
- Current conditions: temperature, humidity, pressure, wind, precipitation, cloud coverage.
- Hourly and daily forecasts with condition mapping.
- Uses Home Assistant location (latitude/longitude).

## Screenshots
Add screenshots to `docs/screenshots/` and link them here. Example paths:
- `docs/screenshots/weather-card.png`
- `docs/screenshots/forecast.png`

## Install with HACS (custom repo)
1. Push this repository to GitHub.
2. In Home Assistant, open HACS.
3. Integrations -> menu -> Custom repositories.
4. Add the repo URL, select type: Integration.
5. Install "Meteomatics Weather" and restart Home Assistant.
6. Add the integration in Settings -> Devices & Services.

## Manual install
1. Copy `custom_components/meteomatics_weather` into your HA config directory.
2. Restart Home Assistant.
3. Add the integration in Settings -> Devices & Services.

## Configure
You will need your Meteomatics username and password. The integration uses the HA location.

## Supported parameters
Default parameters are defined in `custom_components/meteomatics_weather/const.py`.
If your plan does not support a parameter, remove it there or adjust the unit.

## Services and attributes
- `weather.get_forecasts` (hourly/daily) returns forecast entries with `cloud_coverage`.
- Current cloud coverage is available as `cloud_coverage` on the weather entity.

## Troubleshooting
- Authentication error: verify username/password.
- API parameter errors: remove the unsupported parameter or change the unit.
- Missing night icons: ensure weather symbol codes are returned by your plan.

## Notes
- Requires a Meteomatics plan that supports the requested parameters.
- Cloud coverage uses `effective_cloud_cover:p` and maps directly to HA percent values.
