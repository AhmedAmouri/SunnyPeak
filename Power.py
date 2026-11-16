"""Irradiance, temperature, and DC power calculations for a PV panel."""

import numpy as np

from irradiation import calculate_irradiation
from pv_panel import get_panel
from solar import get_solar_angles
from weather import get_weather


def calculate_power(
    beta, gamma, cos_alpha, sin_alpha, cos_gamma_s, sin_gamma_s, dni, dhi,
    T_a, P_i, gamma_c, T_noct, roh, v_w, standoff=2, story=2,
):
    """Return DC watts for prepared weather and sun angles.

    beta and gamma are panel angles in radians. P_i is rated watts divided
    by 1,000, gamma_c is the fractional coefficient per °C, and roh is
    optical efficiency.
    """
    irradiance = calculate_irradiation(
        beta, gamma, cos_alpha, sin_alpha, cos_gamma_s, sin_gamma_s, dni, dhi,
    )
    temperature = get_cell_temperature(T_a, irradiance, T_noct, roh, v_w, standoff, story)
    return power_from_irradiance(irradiance, temperature, P_i, gamma_c)


def power_from_irradiance(I, T, P_i, gamma_c):
    """Convert irradiance in W/m² and cell temperature in °C to panel watts."""
    power = np.zeros_like(I)
    low_light = (I > 0) & (I <= 125)
    bright_light = I > 125

    # The model response is quadratic at low irradiance and linear above it.
    power[low_light] = (
        0.008 * I[low_light] ** 2 * P_i * (1 + (T[low_light] - 25) * gamma_c)
    )
    power[bright_light] = I[bright_light] * P_i * (1 + (T[bright_light] - 25) * gamma_c)
    return power


def get_power(
    latitude, longitude, beta, gamma, time_step, delta_T, year,
    panel_name, standoff=2, story=2,
):
    """Load site weather and return modeled watts per panel for fixed angles."""
    dni, dhi, ambient_temp, wind, utc_offset = get_weather(
        latitude, longitude, year, ("DNI", "DHI", "Temperature", "Wind Speed"),
        time_step, delta_T,
    )
    cos_alt, sin_alt, sin_az, cos_az = get_solar_angles(
        latitude, longitude, utc_offset, time_step, delta_T,
    )
    rated_power, coefficient_pct, efficiency, nominal_temp = get_panel(panel_name)

    return calculate_power(
        beta, gamma, cos_alt, sin_alt, cos_az, sin_az, dni, dhi,
        ambient_temp, rated_power / 1000, coefficient_pct / 100,
        nominal_temp, efficiency / 0.9, wind, standoff, story,
    )


def get_cell_temperature(T_a, I, T_noct, optical_efficiency, v_w, standoff=2, story=2):
    """Estimate cell temperature in °C using mounting clearance in inches."""
    # A smaller gap behind the panel reduces ventilation.
    if standoff > 3.5:
        adjusted_noct = T_noct
    elif standoff >= 2.5:
        adjusted_noct = T_noct + 2
    elif standoff >= 1.5:
        adjusted_noct = T_noct + 6
    elif standoff >= 0.5:
        adjusted_noct = T_noct + 11
    else:
        adjusted_noct = T_noct + 18

    panel_wind = (0.61 if story > 2 else 0.51) * v_w
    return (
        T_a
        + (I / 800) * (adjusted_noct - 20) * (1 - optical_efficiency)
        * (9.5 / (5.7 + 3.8 * panel_wind))
    )
