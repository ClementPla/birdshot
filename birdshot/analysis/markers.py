import numpy as np
import scipy
from birdshot.analysis.filter import low_pass_filter
import matplotlib.pyplot as plt
import streamlit as st


def extract_baseline_value(trial, time=None):
    # The baseline is defined as the mean of the first values where time is negative
    if time is None:
        time = trial[("", "Time (ms)")]
    mask = time < 0
    trial_baseline = trial.loc[mask]
    return trial_baseline.mean()


def extract_scoto_rod_markers(trial, time, time_limits=(10, 150)):
    """
    Extracts the amplitude and time of the peaks in the
    scoto rod analysis. The peaks are defined as the maximum
    value of the signal between time_limits (default 10, 150) ms."""

    mask = (time < time_limits[1]) & (time > time_limits[0])
    org = trial.copy()
    trial = org.loc[mask]

    ymax_value = trial.max(axis=0)
    xmax_value = trial.idxmax(axis=0)

    return ymax_value, xmax_value


def extract_scoto_rod_cone_markers(trial, time, time_limits=(10, 100), delta=0.7):
    """
    Extracts the amplitude and time of the peaks in the
    scoto rod cone analysis. The peaks are defined as the maximum
    and minimum values of the signal between time_limits (default 10, 100) ms for the maximum
    and (time_limits[0], time_limits[1] * delta) for the minimum.
    .
    """
    mask = (time < time_limits[1]) & (time > time_limits[0])
    org = trial.copy()
    trial = org.loc[mask]

    ymax_value = trial.max(axis=0)
    xmax_value = trial.idxmax(axis=0)
    mask = (time < time_limits[1] * delta) & (time > time_limits[0])
    trial = org.loc[mask]
    ymin_value = trial.min(axis=0)
    xmin_value = trial.idxmin(axis=0)
    return ymax_value, ymin_value, xmax_value, xmin_value


@st.cache_data
def extract_scoto_rod_cone_analysis(
    trial,
    filtered=75,
    time_limits=(10, 100),
    plot=False,
    title="",
    return_filtered=False,
):
    org = trial.copy()
    if filtered > 0:
        trial = low_pass_filter(trial, filtered)
    time = trial[("", "Time (ms)")]
    baseline = extract_baseline_value(trial[19], time)
    ymax_value, ymin_value, xmax_value, xmin_value = extract_scoto_rod_cone_markers(
        trial[19], time, time_limits
    )
    A_amplitude = np.abs(ymin_value - baseline)
    B_amplitude = np.abs(ymax_value - ymin_value)

    B_time_od = time.loc[xmax_value["OD"]]
    A_time_od = time.loc[xmin_value["OD"]]

    B_time_os = time.loc[xmax_value["OS"]]
    A_time_os = time.loc[xmin_value["OS"]]

    if plot:
        fig, axs = plt.subplots(1, 2, figsize=(8, 3))
        axs[1].plot(time, trial[(19, "OS")])
        axs[0].plot(time, trial[(19, "OD")])
        if filtered:
            axs[0].plot(time, org[(19, "OD")], alpha=0.5)
            axs[1].plot(time, org[(19, "OS")], alpha=0.5)

        axs[0].axhline(baseline["OD"], color="green", linestyle="--")
        axs[1].axhline(baseline["OS"], color="green", linestyle="--")

        axs[0].scatter(
            B_time_od,
            ymax_value["OD"],
            color="red",
            label=f"OD B - {B_amplitude['OD']:0.1f}",
            zorder=2,
        )
        axs[1].scatter(
            B_time_os,
            ymax_value["OS"],
            color="red",
            label=f"OS B - {B_amplitude['OS']:0.1f}",
            zorder=2,
        )
        axs[0].scatter(
            A_time_od,
            ymin_value["OD"],
            color="green",
            label=f"OD A - {A_amplitude['OD']:0.1f}",
            zorder=2,
        )
        axs[1].scatter(
            A_time_os,
            ymin_value["OS"],
            color="green",
            label=f"OS A - {A_amplitude['OS']:0.1f}",
            zorder=2,
        )
        fig.suptitle(title)
        lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        fig.legend(lines, labels)
        plt.show()
    if return_filtered:
        return (
            B_amplitude,
            A_amplitude,
            B_time_od,
            A_time_od,
            B_time_os,
            A_time_os,
            trial,
        )
    else:
        return B_amplitude, A_amplitude, B_time_od, A_time_od, B_time_os, A_time_os


@st.cache_data
def extract_scoto_rod_analysis(
    trial,
    filtered=100,
    time_limits=(10, 150),
    plot=False,
    title="",
    return_filtered=False,
):
    """
    Extracts the amplitude and time of the peaks in the
    scoto rod analysis. The peaks are defined as the maximum
    value of the signal before 80ms.

    """
    org = trial.copy()
    if filtered > 0:
        trial = low_pass_filter(trial, filtered)
    time = trial[("", "Time (ms)")]
    baseline = extract_baseline_value(trial[9], time)
    ymax_value, xmax_value = extract_scoto_rod_markers(trial[9], time, time_limits)
    B_amplitude = np.abs(ymax_value - baseline)
    B_time_od = time.loc[xmax_value["OD"]]
    B_time_os = time.loc[xmax_value["OS"]]

    if plot:
        fig, axs = plt.subplots(1, 2, figsize=(8, 3))
        axs[1].plot(time, trial[(9, "OS")])
        axs[0].plot(time, trial[(9, "OD")])
        if filtered:
            axs[0].plot(time, org[(9, "OD")], alpha=0.5)
            axs[1].plot(time, org[(9, "OS")], alpha=0.5)

        axs[0].axhline(baseline["OD"], color="green", linestyle="--")
        axs[1].axhline(baseline["OS"], color="green", linestyle="--")

        axs[0].scatter(
            B_time_od,
            ymax_value["OD"],
            color="red",
            label=f"OD B - {B_amplitude['OD']:0.1f}",
            zorder=2,
        )
        axs[1].scatter(
            B_time_os,
            ymax_value["OS"],
            color="red",
            label=f"OS B - {B_amplitude['OS']:0.1f}",
            zorder=2,
        )
        fig.suptitle(title)
        lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        fig.legend(lines, labels)
        plt.show()
    if return_filtered:
        return B_amplitude, B_time_od, B_time_os, trial
    else:
        return B_amplitude, B_time_od, B_time_os


@st.cache_data
def extract_f30_analysis(
    trial,
    filtered=0,
    prominance=10,
    delta=0.4,
    plot=False,
    title="",
    return_peaks=False,
    return_filtered=False,
):
    """
    Extracts the amplitude and time of the peaks in the
    f30 analysis. The peaks are defined as the maximum
    and minimum values of the signal that are separated
    by a time of 1/30 seconds.
    params:
    - trial: pd.DataFrame
    - filtered: int (default 0) - The cutoff frequency of the low pass filter to apply. If 0, no filter is applied
    - prominance: int (default 10) - The prominance of the peaks to find
    - delta: float (default 0.4) - The tolerance of the time between peaks (expected to be at 30Hz +/- delta * 30Hz)
    - plot: bool (default False) - If True, the peaks will be plotted
    - title: str (default "") - The title of the plot
    returns:
    - od_peaks_amplitude: list - The amplitude of the peaks of the OD signal
    - os_peaks_amplitude: list - The amplitude of the peaks of the OS signal
    - od_peaks_time: list - The time of the peaks of the OD signal
    - os_peaks_time: list - The time of the peaks of the OS signal
    """
    time = trial[("", "Time (ms)")]

    # Approximate time between peaks
    T = 1 / 30
    delta = T * delta
    org = trial.copy()
    if filtered > 0:
        trial = low_pass_filter(trial, filtered)

    od = trial[(1, "OD")]
    os = trial[(1, "OS")]

    def get_peaks(data):
        max_peaks, _ = scipy.signal.find_peaks(
            data - data.min(), height=None, prominence=prominance
        )
        min_peaks, _ = scipy.signal.find_peaks(
            -(data - data.min()), prominence=prominance
        )

        # A good peak should have a minimum followed by a maximum
        # We will filter the peaks that do not have this characteristic
        max_peaks = max_peaks[np.where(time.loc[max_peaks] > time.loc[min_peaks[0]])]
        # We make sure that we alternate between max and min peaks
        peaks = []
        for i, min_peak in enumerate(min_peaks):
            if i >= len(max_peaks):
                break
            min_peak_t = time.loc[min_peak]
            max_peak = max_peaks[i]
            max_peak_t = time.loc[max_peak]
            time_diff = (1e-3 * (max_peak_t - min_peak_t)) * 2

            if (time_diff < T - delta) or (time_diff > T + delta):
                continue
            peaks.append((min_peak, max_peak))
        return peaks

    od_peaks = get_peaks(od)
    os_peaks = get_peaks(os)

    od_peaks_amplitude = []
    os_peaks_amplitude = []
    od_peaks_time = []
    os_peaks_time = []

    od_peaks_coords = []
    os_peaks_coords = []

    for min_peak, max_peak in od_peaks:
        od_peaks_amplitude.append(od.loc[max_peak] - od.loc[min_peak])
        od_peaks_time.append(time.loc[max_peak])
        od_peaks_coords.append(
            (od.loc[min_peak], od.loc[max_peak], time.loc[min_peak], time.loc[max_peak])
        )

    for min_peak, max_peak in os_peaks:
        os_peaks_amplitude.append(os.loc[max_peak] - os.loc[min_peak])
        os_peaks_time.append(time.loc[max_peak])
        os_peaks_coords.append(
            (os.loc[min_peak], os.loc[max_peak], time.loc[min_peak], time.loc[max_peak])
        )

    if plot:
        fig, axs = plt.subplots(1, 2, figsize=(8, 3))
        axs[1].plot(time, trial[(1, "OS")])
        axs[0].plot(time, trial[(1, "OD")])
        if filtered > 0:
            axs[0].plot(time, org[(1, "OD")], alpha=0.5)
            axs[1].plot(time, org[(1, "OS")], alpha=0.5)

        for min_peak, max_peak in od_peaks:
            min_t = time.loc[min_peak]
            max_t = time.loc[max_peak]
            axs[0].fill_between(
                [min_t, max_t],
                [trial[(1, "OD")].loc[min_peak], trial[(1, "OD")].loc[min_peak]],
                [trial[(1, "OD")].loc[max_peak], trial[(1, "OD")].loc[max_peak]],
                color="red",
                alpha=0.5,
            )
        for min_peak, max_peak in os_peaks:
            min_t = time.loc[min_peak]
            max_t = time.loc[max_peak]
            axs[1].fill_between(
                [min_t, max_t],
                [trial[(1, "OS")].loc[min_peak], trial[(1, "OS")].loc[min_peak]],
                [trial[(1, "OS")].loc[max_peak], trial[(1, "OS")].loc[max_peak]],
                color="red",
                alpha=0.5,
            )
        fig.suptitle(title)
        plt.show()

    outputs = [od_peaks_amplitude, os_peaks_amplitude, od_peaks_time, os_peaks_time]
    if return_peaks:
        outputs.extend([od_peaks_coords, os_peaks_coords])
    if return_filtered:
        outputs.append(trial)
    return outputs


@st.cache_data
def extract_photo_analysis(trial, plot=False, title=""):
    time = trial[("", "Time (ms)")]
    if plot:
        fig, axs = plt.subplots(1, 2, figsize=(8, 3))
        axs[1].plot(time, trial[(13, "OS")])
        axs[0].plot(time, trial[(13, "OD")])
        axs[1].plot(time, trial[(14, "OS")])
        axs[0].plot(time, trial[(14, "OD")])
        fig.suptitle(title)
        lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        fig.legend(lines, labels)
        plt.show()
