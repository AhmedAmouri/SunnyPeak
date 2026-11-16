"""Choose fixed panel angles for a year of modeled irradiance or power."""

import numpy as np
from scipy.optimize import minimize

from irradiation import calculate_irradiation
from Power import calculate_power
from pv_panel import get_panel
from solar import get_solar_angles
from weather import get_weather


def optimize_orientation(latitude, model, model_inputs):
    """Return tilt and azimuth in radians, plus the model's annual mean."""
    facing_equator = np.pi if latitude >= 0 else 0.0

    def negative_mean(angles):
        return -float(np.mean(model(*angles, *model_inputs)))

    result = minimize(
        negative_mean,
        (0.0, facing_equator),
        bounds=((0.0, np.pi / 2), (facing_equator - np.pi, facing_equator + np.pi)),
    )
    if not result.success:
        raise RuntimeError(f"Solar orientation optimization failed: {result.message}")

    tilt, azimuth = result.x
    return float(tilt), float(azimuth % (2 * np.pi)), -float(result.fun)


def negative_yearly_irradiation_sum(angles, *args):
    """Return the negative sum of the year's irradiance samples."""
    return -np.sum(calculate_irradiation(*angles, *args))


def optimize_yearly_irradiation(latitude, longitude, year, time_step, delta_T):
    """Find fixed angles for a site and return annual mean irradiance in W/m²."""
    dni, dhi, utc_offset = get_weather(
        latitude, longitude, year, ("DNI", "DHI"), time_step, delta_T,
    )
    cos_alt, sin_alt, sin_az, cos_az = get_solar_angles(
        latitude, longitude, utc_offset, time_step, delta_T,
    )
    inputs = (cos_alt, sin_alt, cos_az, sin_az, dni, dhi)
    return optimize_orientation(latitude, calculate_irradiation, inputs)


def negative_yearly_power_sum(angles, *args):
    """Return the negative sum of the year's power samples."""
    # This objective receives solar azimuth sine before cosine.
    (
        cos_alt, sin_alt, sin_az, cos_az, dni, dhi,
        ambient_temp, scaled_power, coefficient, nominal_temp,
        optical_efficiency, wind, standoff, story,
    ) = args
    power = calculate_power(
        *angles, cos_alt, sin_alt, cos_az, sin_az, dni, dhi,
        ambient_temp, scaled_power, coefficient, nominal_temp,
        optical_efficiency, wind, standoff, story,
    )
    return -np.sum(power)


def optimize_yearly_power(
    latitude, longitude, year, time_step, delta_T, panel_name, standoff=2, story=2,
):
    """Find fixed angles for a catalog panel and return annual mean watts."""
    dni, dhi, ambient_temp, wind, utc_offset = get_weather(
        latitude, longitude, year, ("DNI", "DHI", "Temperature", "Wind Speed"),
        time_step, delta_T,
    )
    cos_alt, sin_alt, sin_az, cos_az = get_solar_angles(
        latitude, longitude, utc_offset, time_step, delta_T,
    )
    rated_power, coefficient_pct, efficiency, nominal_temp = get_panel(panel_name)

    inputs = (
        cos_alt, sin_alt, cos_az, sin_az, dni, dhi,
        ambient_temp, rated_power / 1000, coefficient_pct / 100,
        nominal_temp, efficiency / 0.9, wind, standoff, story,
    )
    return optimize_orientation(latitude, calculate_power, inputs)
