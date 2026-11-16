"""Load and interpolate cached NSRDB weather data for the solar models."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import pandas as pd

WEATHER_DIR = Path(__file__).resolve().parent / "data" / "weather"
MINUTES_PER_YEAR = 365 * 24 * 60
BASE_URL = (
    "https://developer.nlr.gov/api/nsrdb/v2/solar/"
    "nsrdb-msg-v1-0-0-download.csv"
)


def get_weather(latitude, longitude, year, data, time_step, delta_T):
    """Return the requested weather arrays followed by the local UTC offset."""
    filename = f"year_{year}_interval_{delta_T}.csv"
    wkt = f"POINT({longitude} {latitude})"
    weather_file = WEATHER_DIR / wkt / filename
    if not weather_file.is_file():
        lon = str(float(longitude)).removesuffix(".0")
        lat = str(float(latitude)).removesuffix(".0")
        wkt = f"POINT({lon} {lat})"
        weather_file = WEATHER_DIR / wkt / filename
        if not weather_file.is_file():
            download_nsrdb_data(year, delta_T, wkt)

    metadata = pd.read_csv(weather_file, nrows=1)
    delta_UTC = metadata.iloc[0]["Local Time Zone"]
    weather_df = pd.read_csv(weather_file, skiprows=2)
    weather = [
        interpolate_data(weather_df[param].to_numpy(dtype=float), time_step, delta_T)
        for param in data
    ]
    return [*weather, delta_UTC]


def interpolate_data(original_values, time_step, delta_T):
    """Linearly interpolate a 365-day weather series onto the simulation grid."""
    start = 30 if delta_T == 60 else 0
    source_minutes = np.arange(start, MINUTES_PER_YEAR, delta_T)
    if len(original_values) != len(source_minutes):
        raise ValueError(
            f"Expected {len(source_minutes):,} weather samples at {delta_T}-minute "
            f"intervals, received {len(original_values):,}."
        )
    if not np.all(np.isfinite(original_values)):
        raise ValueError("Weather data contains missing or non-finite measurements.")
    return np.interp(
        np.arange(0, MINUTES_PER_YEAR, time_step),
        source_minutes,
        original_values,
    )


def download_nsrdb_data(year, delta_T, wkt):
    """Download a missing NSRDB CSV and write it atomically to the cache."""
    api_key = os.environ.get("NSRDB_API_KEY", "").strip()
    email = os.environ.get("NSRDB_EMAIL", "").strip()
    if not api_key or not email:
        raise FileNotFoundError(
            f"No bundled weather for {wkt}, {year}, {delta_T}-minute intervals. "
            "Set NSRDB_API_KEY and NSRDB_EMAIL to download weather for supported locations."
        )

    import requests

    params = {
        "api_key": api_key,
        "email": email,
        "wkt": wkt,
        "attributes": "dhi,dni,air_temperature,wind_speed",
        "names": year,
        "utc": "false",
        "leap_day": "false",
        "interval": delta_T,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=(10, 120))
    except requests.RequestException as error:
        raise RuntimeError(f"NSRDB request failed ({type(error).__name__}).") from None
    if response.status_code != 200:
        raise RuntimeError(f"NSRDB HTTP {response.status_code}.")

    folder = WEATHER_DIR / wkt
    folder.mkdir(parents=True, exist_ok=True)
    filename = folder / f"year_{year}_interval_{delta_T}.csv"
    with NamedTemporaryFile(dir=folder, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            temporary.write(response.content)
            temporary.close()
            temporary_path.replace(filename)
        finally:
            temporary_path.unlink(missing_ok=True)
