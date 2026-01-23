# Meteomatics Weather

Custom Home Assistant integration for Meteomatics weather data (current, hourly, daily).

## Install with HACS (custom repo)
1. Push this repository to GitHub.
2. In Home Assistant, open HACS.
3. Integrations -> menu -> Custom repositories.
4. Add the repo URL, select type: Integration.
5. Install "Meteomatics Weather" and restart Home Assistant.
6. Add the integration in Settings -> Devices & Services.

## Configure
You will need your Meteomatics username and password.

## Notes
- Uses the Home Assistant location for latitude/longitude.
- Requires a Meteomatics plan that supports the requested parameters.
