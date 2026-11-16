"""Public API for historical solar panel simulations."""

from collections.abc import Mapping
from datetime import timedelta, timezone
from math import degrees, isfinite, radians
from numbers import Integral
from typing import Literal

import numpy as np
import pandas as pd

from irradiation import calculate_irradiation
from optimize import optimize_orientation
from Power import calculate_power, get_cell_temperature, power_from_irradiance
from pv_panel import resolve_panel
from solar import get_solar_angles
from weather import get_weather


def _summarize(timeseries: pd.DataFrame, frequency: str) -> pd.DataFrame:
    return timeseries.resample(frequency).agg(
        energy_kwh=("energy_kwh", "sum"),
        irradiation_kwh_m2=("irradiation_kwh_m2", "sum"),
        mean_power_w=("power_w", "mean"),
        mean_irradiance_w_m2=("irradiance_w_m2", "mean"),
    ).dropna(subset=["mean_power_w"])


def simulate_solar(
    latitude: float,
    longitude: float,
    year: int | str,
    *,
    panel_name: str | None = None,
    panel_spec: Mapping[str, float] | None = None,
    panel_count: int = 1,
    tilt_deg: float | None = None,
    azimuth_deg: float | None = None,
    optimize_for: Literal["power", "irradiance"] | None = None,
    time_step_minutes: int = 15,
    weather_interval_minutes: int = 15,
    standoff_inches: float = 2.0,
    building_stories: int = 2,
) -> dict:
    """Simulate 365 days of solar output for a site and weather year.

    Supply latitude and longitude in decimal degrees and a historical
    weather year. Pass both tilt_deg (0–90 from horizontal) and azimuth_deg
    (0 north, 90 east, 180 south, 270 west) for a fixed orientation. With
    both angles omitted, the function optimizes for power by default.
    Pass optimize_for="irradiance" to maximize sunlight on the panel.

    Supply a dictionary of datasheet values as panel_spec, or select a
    model with panel_name. All panels share the same orientation. The result
    dictionary contains the angles, annual totals, and time series, daily,
    and monthly tables. Timestamps are in local standard time and omit
    February 29.
    """
    latitude, longitude = float(latitude), float(longitude)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Latitude must be within ±90° and longitude within ±180°.")
    year_text = str(year)
    if len(year_text) != 4 or not year_text.isascii() or not year_text.isdecimal():
        raise ValueError("year must be a four-digit calendar year.")
    year = int(year_text)
    if not 1 <= year <= 9998:
        raise ValueError("year must be a valid calendar year.")
    if isinstance(panel_count, bool) or not isinstance(panel_count, Integral) or panel_count < 1:
        raise ValueError("panel_count must be a positive integer.")
    if (
        isinstance(time_step_minutes, bool)
        or not isinstance(time_step_minutes, Integral)
        or time_step_minutes < 1
        or (24 * 60) % time_step_minutes
    ):
        raise ValueError("time_step_minutes must be a positive integer that divides 1,440.")
    if not isinstance(weather_interval_minutes, Integral) or weather_interval_minutes not in (15, 30, 60):
        raise ValueError("weather_interval_minutes must be 15, 30 or 60.")
    if (tilt_deg is None) != (azimuth_deg is None):
        raise ValueError("Pass both tilt_deg and azimuth_deg, or omit both to optimize.")
    if optimize_for not in (None, "power", "irradiance"):
        raise ValueError('optimize_for must be "power" or "irradiance".')
    if tilt_deg is not None:
        if optimize_for is not None:
            raise ValueError("Choose fixed angles or an optimization objective.")
        tilt_deg, azimuth_deg = float(tilt_deg), float(azimuth_deg)
        if not (0 <= tilt_deg <= 90 and isfinite(azimuth_deg)):
            raise ValueError("Tilt must be within 0–90° and azimuth must be finite.")
        azimuth_deg %= 360
    if not isfinite(standoff_inches) or standoff_inches < 0:
        raise ValueError("standoff_inches must be finite and nonnegative.")
    if isinstance(building_stories, bool) or not isinstance(building_stories, Integral) or building_stories < 1:
        raise ValueError("building_stories must be a positive integer.")

    panel_name, rated_power, temp_coefficient, efficiency, nominal_temp = resolve_panel(
        panel_name, panel_spec,
    )

    dni, dhi, ambient_temp, wind, utc_offset = get_weather(
        latitude, longitude, year, ("DNI", "DHI", "Temperature", "Wind Speed"),
        time_step_minutes, weather_interval_minutes,
    )
    cos_alt, sin_alt, sin_az, cos_az = get_solar_angles(
        latitude, longitude, utc_offset, time_step_minutes, weather_interval_minutes,
    )
    irradiance_inputs = (cos_alt, sin_alt, cos_az, sin_az, dni, dhi)
    optical_efficiency = efficiency / 0.9
    power_per_irradiance = rated_power / 1000
    temp_coefficient /= 100
    if tilt_deg is None:
        optimize_for = optimize_for or "power"
        if optimize_for == "power":
            power_inputs = (
                *irradiance_inputs, ambient_temp, power_per_irradiance,
                temp_coefficient, nominal_temp, optical_efficiency, wind,
                standoff_inches, building_stories,
            )
            beta, gamma, _ = optimize_orientation(latitude, calculate_power, power_inputs)
        else:
            beta, gamma, _ = optimize_orientation(latitude, calculate_irradiation, irradiance_inputs)
        tilt_deg, azimuth_deg = degrees(beta), -degrees(gamma) % 360
    else:
        # The original solar model measures azimuth westward from north.
        beta, gamma = radians(tilt_deg), -radians(azimuth_deg)

    irradiance = calculate_irradiation(beta, gamma, *irradiance_inputs)
    cell_temp = get_cell_temperature(
        ambient_temp, irradiance, nominal_temp, optical_efficiency, wind,
        standoff_inches, building_stories,
    )
    power = panel_count * power_from_irradiance(
        irradiance, cell_temp, power_per_irradiance, temp_coefficient,
    )
    local_time = timezone(timedelta(hours=float(utc_offset)))
    timestamps = pd.date_range(
        f"{year}-01-01", f"{year + 1}-01-01",
        freq=f"{time_step_minutes}min", tz=local_time, inclusive="left",
        name="timestamp",
    )
    timestamps = timestamps[~((timestamps.month == 2) & (timestamps.day == 29))]
    to_kwh = time_step_minutes / 60_000
    timeseries = pd.DataFrame(
        {
            "power_w": power,
            "irradiance_w_m2": irradiance,
            "cell_temperature_c": cell_temp,
            "energy_kwh": power * to_kwh,
            "irradiation_kwh_m2": irradiance * to_kwh,
        },
        index=timestamps,
    )
    daily = _summarize(timeseries, "D")
    monthly = _summarize(timeseries, "MS")
    return {
        "latitude": latitude,
        "longitude": longitude,
        "year": year,
        "panel_name": panel_name,
        "panel_count": int(panel_count),
        "tilt_deg": tilt_deg,
        "azimuth_deg": azimuth_deg,
        "optimized_for": optimize_for,
        "time_step_minutes": int(time_step_minutes),
        "annual_kwh": float(monthly["energy_kwh"].sum()),
        "annual_irradiation_kwh_m2": float(monthly["irradiation_kwh_m2"].sum()),
        "timeseries": timeseries,
        "daily": daily,
        "monthly": monthly,
    }
