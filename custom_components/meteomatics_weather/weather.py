"""Weather platform for Meteomatics."""
from __future__ import annotations

from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_NAME, DEFAULT_NAME, DOMAIN
from .coordinator import MeteomaticsDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MeteomaticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    async_add_entities([MeteomaticsWeather(coordinator, name)])


class MeteomaticsWeather(
    CoordinatorEntity[MeteomaticsDataUpdateCoordinator], WeatherEntity
):
    """Representation of Meteomatics weather."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = False
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_native_precipitation_unit = UnitOfLength.MILLIMETERS
    _attr_forecast_hourly = None
    _attr_forecast_daily = None
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
    )

    def __init__(self, coordinator: MeteomaticsDataUpdateCoordinator, name: str) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_weather"
        self._attr_forecast_hourly = None
        self._attr_forecast_daily = None

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data or {}
        current = data.get("current", {})

        self._attr_condition = current.get("condition")
        self._attr_native_temperature = current.get("temperature")
        self._attr_humidity = current.get("humidity")
        self._attr_native_pressure = current.get("pressure")
        self._attr_wind_speed = current.get("wind_speed")
        self._attr_wind_bearing = current.get("wind_bearing")
        self._attr_native_precipitation = current.get("precipitation")
        self._attr_cloud_coverage = current.get("cloud_coverage")
        self._attr_forecast_hourly = data.get("hourly")
        self._attr_forecast_daily = data.get("daily")

        super()._handle_coordinator_update()

    @property
    def forecast_hourly(self):
        return self._attr_forecast_hourly

    @property
    def forecast_daily(self):
        return self._attr_forecast_daily

    async def async_forecast_hourly(self):
        data = self.coordinator.data or {}
        return data.get("hourly") or []

    async def async_forecast_daily(self):
        data = self.coordinator.data or {}
        return data.get("daily") or []
