"""Summaries and date slices for a 365-day simulation series."""

import numpy as np


DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MINUTES_PER_DAY = 24 * 60


def average_over_period(data_list, delta_T, period_days=7):
    """Average complete blocks of days using a sample interval that divides 60 minutes."""
    samples = np.asarray(data_list)
    samples_per_period = (60 // delta_T) * 24 * period_days
    complete_samples = len(samples) // samples_per_period * samples_per_period
    periods = samples[:complete_samples].reshape(-1, samples_per_period)
    return np.mean(periods, axis=1)


def monthly_averages(data, delta_T):
    """Return a mean for each calendar month, starting with January."""
    averages = np.zeros(12)
    start = 0
    for month, days in enumerate(DAYS_IN_MONTH):
        end = start + days * MINUTES_PER_DAY // delta_T
        averages[month] = np.mean(data[start:end])
        start = end
    return averages


def get_values_for_period(data, delta_T, start_date, end_date):
    """Slice a 365-day series between two dd/mm dates, excluding the end date."""
    start_day, start_month = map(int, start_date.split("/"))
    end_day, end_month = map(int, end_date.split("/"))
    start = (
        sum(DAYS_IN_MONTH[:start_month - 1]) * MINUTES_PER_DAY // delta_T
        + (start_day - 1) * MINUTES_PER_DAY // delta_T
    )
    end = (
        sum(DAYS_IN_MONTH[:end_month - 1]) * MINUTES_PER_DAY // delta_T
        + (end_day - 1) * MINUTES_PER_DAY // delta_T
    )
    return data[start:end]
