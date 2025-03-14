import pandas as pd
import scipy.signal


def low_pass_filter(trial: pd.DataFrame, cutoff):
    trial = trial.copy()
    N = len(trial)
    time = trial[("", "Time (ms)")]
    fs = N / (time.iloc[-1] - time.iloc[0]) * 1000

    b, a = scipy.signal.butter(5, cutoff / (fs / 2), btype="low")

    for c in trial.columns:
        if c == ("", "Time (ms)"):
            continue
        trial[c] = scipy.signal.filtfilt(b, a, trial[c])

    return trial
