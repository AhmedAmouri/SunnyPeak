"""Estimate irradiance on the plane of an inclined panel."""

from math import cos, sin

import numpy as np

from solar import get_solar_angles
from weather import get_weather


def calculate_irradiation(beta, gamma, cos_alpha, sin_alpha, cos_gamma_s, sin_gamma_s, dni, dhi):
    """Combine direct, diffuse, and ground-reflected irradiance in W/m².

    beta and gamma are panel tilt and azimuth in radians. DNI and DHI are
    direct normal and diffuse horizontal irradiance in W/m².
    """
    cos_tilt = cos(beta)
    sin_tilt = sin(beta)
    cos_heading = cos(gamma)
    sin_heading = sin(gamma)

    incidence = cos_tilt * sin_alpha + sin_tilt * cos_alpha * (
        cos_heading * cos_gamma_s + sin_heading * sin_gamma_s
    )
    direct = dni * np.where(sin_alpha > 0, np.maximum(incidence, 0), 0)
    diffuse = dhi * (1 + cos_tilt) / 2

    horizontal = dhi + dni * np.maximum(sin_alpha, 0)
    reflected = 0.1 * horizontal * (1 - cos_tilt) / 2
    return direct + diffuse + reflected


def get_irradiation(latitude, longitude, beta, gamma, delta_T, time_step, year):
    """Load site weather and return panel-plane irradiance in W/m²."""
    dni, dhi, utc_offset = get_weather(
        latitude, longitude, year, ("DNI", "DHI"), time_step, delta_T,
    )
    cos_alt, sin_alt, sin_az, cos_az = get_solar_angles(
        latitude, longitude, utc_offset, time_step, delta_T,
    )
    return calculate_irradiation(beta, gamma, cos_alt, sin_alt, cos_az, sin_az, dni, dhi)
