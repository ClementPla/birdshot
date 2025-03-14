import streamlit as st
import plotly.express as px
import numpy as np
from birdshot.analysis.markers import (
    extract_f30_analysis,
    extract_scoto_rod_analysis,
    extract_baseline_value,
    extract_scoto_rod_cone_analysis,
)


def plot_f30_progression(data, f30_low_pass, f30_prominance, f30_delta):
    meanAmplitudes = dict(OS=dict(), OD=dict())
    stdAmplitudes = dict(OS=dict(), OD=dict())
    for visit in data:
        try:
            od_peaks_amplitude, os_peaks_amplitude, od_peaks_time, os_peaks_time = (
                extract_f30_analysis(
                    data[visit].copy(),
                    filtered=f30_low_pass,
                    prominance=f30_prominance,
                    delta=f30_delta,
                    plot=False,
                    return_peaks=False,
                    return_filtered=False,
                )
            )
            meanAmplitudes["OD"][visit] = np.mean(od_peaks_amplitude)
            meanAmplitudes["OS"][visit] = np.mean(os_peaks_amplitude)
            stdAmplitudes["OD"][visit] = np.std(od_peaks_amplitude)
            stdAmplitudes["OS"][visit] = np.std(os_peaks_amplitude)

        except Exception as e:
            st.warning(f"Error while extracting markers: {e}")

    col1, col2 = st.columns(2)
    for laterality, col in zip(["OD", "OS"], [col1, col2]):
        ys = []
        xs = []
        xoffset = 0
        for visit in data:
            ys.append(data[visit][1, laterality].values)

            xs.append(np.arange(len(ys[-1])) + xoffset)
            xoffset += len(ys[-1]) + 100

        ys = np.concatenate(ys)
        xs = np.concatenate(xs)

        fig = px.line(
            x=xs,
            y=ys,
            title=laterality,
        )
        fig.update_yaxes(range=[-150, 150])

        with col:
            st.plotly_chart(fig)

        if meanAmplitudes[laterality]:
            progress = px.line(
                x=list(meanAmplitudes[laterality].keys()),
                y=list(meanAmplitudes[laterality].values()),
                title=f"Mean Amplitude {laterality}",
            )
            progress.update_yaxes(range=[-150, 150])
            progress.update_traces(
                error_y=dict(
                    type="data",
                    array=list(stdAmplitudes[laterality].values()),
                    visible=True,
                )
            )
            with col:
                st.plotly_chart(progress)
