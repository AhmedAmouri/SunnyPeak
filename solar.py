"""Approximate the sun's position on a local-standard-time grid."""

import numpy as np


MINUTES_PER_DAY = 24 * 60


def solar_angles(cos_latitude, sin_latitude, longitude, time, delta_UTC):
    """Return cos/sin of sun altitude and sin/cos of sun azimuth.

    time contains minutes from January 1. Longitude is in degrees, and
    delta_UTC is the local standard time offset in hours.
    """
    day_of_year = time // MINUTES_PER_DAY + 1
    seasonal_angle = (np.pi / 180) * (day_of_year - 81)
    declination = 0.4092797095926703 * np.sin(seasonal_angle)
    sin_declination = np.sin(declination)
    cos_declination = np.cos(declination)

    correction_hours = (
        4 * (longitude - 15 * delta_UTC)
        + 9.87 * np.sin(2 * seasonal_angle)
        - 7.53 * np.cos(seasonal_angle)
        - 1.5 * np.sin(seasonal_angle)
    ) / 60
    hour_angle = (np.pi / 12) * (time % MINUTES_PER_DAY / 60 + correction_hours - 12)

    sin_altitude = np.clip(
        cos_latitude * cos_declination * np.cos(hour_angle) + sin_declination * sin_latitude,
        -1, 1,
    )
    cos_altitude = np.cos(np.arcsin(sin_altitude))

    # The solar model measures azimuth westward from north.
    cos_azimuth = np.clip(
        (sin_declination - sin_latitude * sin_altitude) / (cos_latitude * cos_altitude),
        -1, 1,
    )
    sin_azimuth = np.sin(np.sign(hour_angle) * np.arccos(cos_azimuth))
    return np.array([cos_altitude, sin_altitude, sin_azimuth, cos_azimuth])


def get_solar_angles(latitude, longitude, delta_UTC, time_step, delta_T):
    """Calculate sun angles on a 365-day grid at time_step-minute spacing."""
    latitude = np.deg2rad(latitude)
    minutes = np.arange(0, 365 * MINUTES_PER_DAY, time_step, dtype=int)
    return solar_angles(np.cos(latitude), np.sin(latitude), longitude, minutes, delta_UTC)
