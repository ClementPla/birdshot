import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
from birdshot.analysis.markers import (
    extract_f30_analysis,
    extract_scoto_rod_analysis,
    extract_baseline_value,
    extract_scoto_rod_cone_analysis,
)
from birdshot.utils.st_chart import add_fill_between


def plot_f30_progression(data, normal_data, f30_low_pass, f30_prominance, f30_delta):
    meanAmplitudes = dict(OS=dict(), OD=dict())
    stdAmplitudes = dict(OS=dict(), OD=dict())
    for visit in data:
        x = data[visit][("", "Time (ms)")]
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
        fig = go.Figure()
        xoffset = 0
        for visit in data:
            fig.add_trace(
                go.Scatter(
                    x=x + xoffset,
                    y=data[visit][1, laterality].values,
                    name=visit,
                )
            )
            xoffset += (x.max() - x.min()) * 1.2

        fig.update_yaxes(range=[-150, 150])
        # Set the title of the graph

        fig.update_layout(title=f"F30 {laterality}")
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


def plot_scoto_rod_progression(
    data,
    normal_data,
    rodOnly=True,
    scotorodcone_low_pass=75,
    scotorodcone_time_limits=(10, 60),
    scotorod_low_pass=75,
    scotorod_time_limits=(10, 125),
):
    if rodOnly:
        plot_scoto_rod(data, normal_data, scotorod_low_pass, scotorod_time_limits)
    else:
        plot_scoto_rodcone(
            data, normal_data, scotorodcone_low_pass, scotorodcone_time_limits
        )


def plot_scoto_rodcone(
    data, normal_data, scotorodcone_low_pass, scotorodcone_time_limits
):
    amplitudeA = dict(OS=dict(), OD=dict())
    amplitudeB = dict(OS=dict(), OD=dict())
    timeA = dict(OS=dict(), OD=dict())
    timeB = dict(OS=dict(), OD=dict())
    col1, col2 = st.columns(2)
    for visit in data:
        B_amplitude, A_amplitude, B_time_od, A_time_od, B_time_os, A_time_os = (
            extract_scoto_rod_cone_analysis(
                data[visit].copy(),
                plot=False,
                time_limits=scotorodcone_time_limits,
                return_filtered=False,
                filtered=scotorodcone_low_pass,
            )
        )

        amplitudeA["OD"][visit] = A_amplitude["OD"]
        amplitudeA["OS"][visit] = A_amplitude["OS"]

        amplitudeB["OD"][visit] = B_amplitude["OD"]
        amplitudeB["OS"][visit] = B_amplitude["OS"]
        timeA["OD"][visit] = A_time_od
        timeA["OS"][visit] = A_time_os
        timeB["OD"][visit] = B_time_od
        timeB["OS"][visit] = B_time_os

    N = len(data[visit])

    for laterality, col in zip(["OD", "OS"], [col1, col2]):
        normal_values = np.asarray(
            [
                r[19, laterality].values
                for r in normal_data
                if len(r[19, laterality].values) == N
            ]
        )

        mean_normal = np.mean(normal_values, axis=0)
        std_normal = np.std(normal_values, axis=0)

        fig = go.Figure()
        x = data[visit][("", "Time (ms)")]
        offset = 0
        for visit in data:
            fig.add_trace(
                go.Scatter(
                    x=x + offset,
                    y=data[visit][19, laterality].values,
                    name=visit,
                )
            )
            add_fill_between(
                fig,
                mean_normal,
                std_normal,
                time=x + offset,
                std_mult=2.0,
                color="rgba(0,115,0,0.2)",
                showlegend=False,
            )
            add_fill_between(
                fig,
                mean_normal,
                std_normal,
                time=x + offset,
                std_mult=1.0,
                color="rgba(0,150,0,0.25)",
                showlegend=False,
            )
            add_fill_between(
                fig,
                mean_normal,
                std_normal,
                time=x + offset,
                std_mult=0.5,
                color="rgba(0,225,0,0.3)",
                showlegend=False,
            )

            offset += (x.max() - x.min()) * 1.25

        fig.update_yaxes(range=[-250, 250])
        fig.update_layout(title=f"Scotopic rod-cone progression {laterality}")
        with col:
            st.plotly_chart(fig)

        progress = make_subplots(specs=[[{"secondary_y": True}]])
        progress.add_trace(
            go.Scatter(
                x=list(amplitudeA[laterality].keys()),
                y=list(amplitudeA[laterality].values()),
                name=f"Amplitude A {laterality}",
            ),
            secondary_y=False,
        )

        progress.add_trace(
            go.Scatter(
                x=list(amplitudeB[laterality].keys()),
                y=list(amplitudeB[laterality].values()),
                name=f"Amplitude B {laterality}",
            ),
            secondary_y=False,
        )

        progress.add_trace(
            go.Scatter(
                x=list(timeA[laterality].keys()),
                y=list(timeA[laterality].values()),
                name=f"φA {laterality}",
            ),
            secondary_y=True,
        )

        progress.add_trace(
            go.Scatter(
                x=list(timeB[laterality].keys()),
                y=list(timeB[laterality].values()),
                name=f"φB {laterality}",
            ),
            secondary_y=True,
        )

        progress.update_yaxes(range=[0, 400], secondary_y=False)
        progress.update_yaxes(range=[0, 150], secondary_y=True)
        progress.update_layout(
            title=f"Scotopic rod-cone Markers progression {laterality}"
        )
        progress.update_yaxes(
            title_text="Time (ms)",
            secondary_y=True,
            title_font_color="red",
        )
        progress.update_yaxes(
            title_text="Amplitude (uV)",
            secondary_y=False,
            title_font_color="blue",
        )

        with col:
            st.plotly_chart(progress)


def plot_scoto_rod(data, normal_data, scotorod_low_pass, scotorod_time_limits):
    amplitude = dict(OS=dict(), OD=dict())
    time = dict(OS=dict(), OD=dict())
    col1, col2 = st.columns(2)

    for visit in data:
        amplitudes, od_peaks_time, os_peaks_time = extract_scoto_rod_analysis(
            data[visit].copy(),
            plot=False,
            time_limits=scotorod_time_limits,
            return_filtered=False,
            filtered=scotorod_low_pass,
        )

        amplitude["OD"][visit] = amplitudes["OD"]
        amplitude["OS"][visit] = amplitudes["OS"]
        time["OD"][visit] = od_peaks_time
        time["OS"][visit] = os_peaks_time

    N = len(data[visit])

    for laterality, col in zip(["OD", "OS"], [col1, col2]):
        normal_values = np.asarray(
            [
                r[9, laterality].values
                for r in normal_data
                if len(r[9, laterality].values) == N
            ]
        )
        mean_normal = np.mean(normal_values, axis=0)
        std_normal = np.std(normal_values, axis=0)

        fig = go.Figure()
        xoffset = 0
        for visit in data:
            x = data[visit][("", "Time (ms)")]
            fig.add_trace(
                go.Scatter(
                    x=x + xoffset,
                    y=data[visit][9, laterality].values,
                    name=visit,
                )
            )
            add_fill_between(
                fig,
                mean_normal,
                std_normal,
                time=x + xoffset,
                std_mult=2.0,
                color="rgba(0,115,0,0.2)",
                showlegend=False,
            )
            add_fill_between(
                fig,
                mean_normal,
                std_normal,
                time=x + xoffset,
                std_mult=1.0,
                color="rgba(0,150,0,0.25)",
                showlegend=False,
            )
            add_fill_between(
                fig,
                mean_normal,
                std_normal,
                time=x + xoffset,
                std_mult=0.5,
                color="rgba(0,225,0,0.3)",
                showlegend=False,
            )

            xoffset += (x.max() - x.min()) * 1.5

        fig.update_yaxes(range=[-250, 250])
        fig.update_layout(title=f"Scotopic rod progression {laterality}")
        with col:
            st.plotly_chart(fig)
        progress = make_subplots(specs=[[{"secondary_y": True}]])

        progress.add_trace(
            go.Scatter(
                x=list(amplitude[laterality].keys()),
                y=list(amplitude[laterality].values()),
                name=f"Amplitude B {laterality}",
            ),
            secondary_y=False,
        )

        progress.add_trace(
            go.Scatter(
                x=list(time[laterality].keys()),
                y=list(time[laterality].values()),
                name=f"φB {laterality}",
            ),
            secondary_y=True,
        )
        progress.update_yaxes(range=[-250, 250], secondary_y=False)
        progress.update_yaxes(range=[25, 150], secondary_y=True)

        progress.update_layout(title=f"Scotopic rod progression {laterality}")
        progress.update_yaxes(title_text="Time (ms)", secondary_y=True)
        progress.update_yaxes(title_text="Amplitude (uV)", secondary_y=False)

        with col:
            st.plotly_chart(progress)


def plot_photo_progress(data, normal_data, steps):
    col1, col2 = st.columns(2)

    for _, d in data.items():
        N = len(d)
        break

    for laterality, col in zip(["OD", "OS"], [col1, col2]):
        fig = go.Figure()
        xoffset = 0

        normal_values = np.asarray(
            [
                r[laterality].values
                for r in normal_data
                if len(r[laterality].values) == N
            ]
        )

        mean_normal = np.mean(normal_values, axis=0)
        std_normal = np.std(normal_values, axis=0)

        for visit, step in zip(data, steps):
            x = data[visit][("", "Time (ms)")]
            fig.add_trace(
                go.Scatter(
                    x=x + xoffset,
                    y=data[visit][step, laterality].values,
                    name=visit,
                )
            )

            add_fill_between(
                fig,
                mean_normal,
                std_normal,
                time=x + xoffset,
                std_mult=2.0,
                color="rgba(0,115,0,0.2)",
                showlegend=False,
            )
            add_fill_between(
                fig,
                mean_normal,
                std_normal,
                time=x + xoffset,
                std_mult=1.0,
                color="rgba(0,150,0,0.25)",
                showlegend=False,
            )
            add_fill_between(
                fig,
                mean_normal,
                std_normal,
                time=x + xoffset,
                std_mult=0.5,
                color="rgba(0,225,0,0.3)",
                showlegend=False,
            )

            xoffset += (x.max() - x.min()) * 1.5

        fig.update_yaxes(range=[-250, 250])
        fig.update_layout(title=f"Photopic progression {laterality}")
        with col:
            st.plotly_chart(fig)
