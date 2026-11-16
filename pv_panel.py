"""Read and extend the panel catalog."""

from math import isfinite
from pathlib import Path

import pandas as pd


PANELS_CSV = Path(__file__).resolve().parent / "data" / "panels.csv"
PANEL_FIELDS = (
    "rated_power_w",
    "temperature_coefficient_pct_per_c",
    "efficiency",
    "nominal_cell_temperature_c",
)
CATALOG_FIELDS = ["Pmax", "Temp_Coeff", "Efficiency", "T_NOCT"]


def resolve_panel(panel_name, panel_spec):
    """Return the display name and four datasheet values for a model."""
    if panel_spec is None:
        panel_name = panel_name or "PV-MJT250GB"
        values = get_panel(panel_name, interactive=False)
    else:
        panel_name = panel_name or "Custom panel"
        try:
            values = tuple(float(panel_spec[field]) for field in PANEL_FIELDS)
        except KeyError as error:
            raise ValueError(f"panel_spec is missing {error.args[0]!r}.") from None
        except (TypeError, ValueError):
            raise ValueError("panel_spec must map each datasheet field to a number.") from None

    rated_power, coefficient, efficiency, nominal_temp = values
    if not (isfinite(rated_power) and rated_power > 0 and 0 < efficiency <= 1):
        raise ValueError("Panel rated power must be positive and efficiency must be a fraction in (0, 1].")
    if not (isfinite(coefficient) and isfinite(nominal_temp)):
        raise ValueError("Panel temperature coefficient and nominal cell temperature must be finite.")

    return panel_name, rated_power, coefficient, efficiency, nominal_temp


def get_panel(panel_name, *, interactive=True):
    """Return rated W, temperature coefficient in %/°C, efficiency, and NOCT in °C."""
    while True:
        catalog = pd.read_csv(PANELS_CSV)
        matches = catalog.loc[catalog["Panel"] == panel_name, CATALOG_FIELDS]
        if not matches.empty:
            return tuple(matches.iloc[0])

        if not interactive:
            available = ", ".join(catalog["Panel"])
            raise ValueError(f"Unknown panel {panel_name!r}. Available panel models: {available}.")

        add_panel(panel_name)


def add_panel(panel_name):
    """Prompt for the datasheet values and save them under panel_name."""
    try:
        rated_power = float(input("Rated power in watts: "))
        coefficient = float(input("Power temperature coefficient in percent per °C: "))
        efficiency = float(input("Efficiency as a fraction, such as 0.21: "))
        nominal_temp = float(input("Nominal operating cell temperature in °C: "))
    except ValueError:
        print("Enter a number for each value.")
        return

    panel = {
        "Panel": panel_name,
        "Pmax": rated_power,
        "Temp_Coeff": coefficient,
        "Efficiency": efficiency,
        "T_NOCT": nominal_temp,
    }
    catalog = pd.read_csv(PANELS_CSV)
    updated_catalog = pd.concat([catalog, pd.DataFrame([panel])], ignore_index=True)
    updated_catalog.to_csv(PANELS_CSV, index=False)
    print(f"Added {panel_name!r} to the panel catalog.")
