"""Plots for a completed SunnyPeak simulation."""


def plot_solar(result):
    """Return a figure with daily and monthly energy and two power profiles."""
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(2, 2, figsize=(11, 6), layout="constrained")

    daily = result["daily"]["energy_kwh"]
    axes[0, 0].plot(daily.index, daily)
    axes[0, 0].set(title="Daily energy", ylabel="kWh")

    monthly = result["monthly"]["energy_kwh"]
    axes[0, 1].bar(monthly.index.strftime("%b"), monthly)
    axes[0, 1].set(title="Monthly energy", ylabel="kWh")

    year = result["year"]
    power = result["timeseries"]["power_w"]
    for axis, month, label in zip(axes[1], ("02", "07"), ("Feb", "Jul")):
        window = power.loc[f"{year}-{month}-01":f"{year}-{month}-10"]
        axis.plot(window.index, window)
        axis.set(title=f"{label} 1–10", ylabel="DC power (W)")

    return figure
