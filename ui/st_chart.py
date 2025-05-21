import streamlit as st
import plotly.express as px
from birdshot.analysis.markers import (
    extract_f30_analysis,
    extract_scoto_rod_analysis,
    extract_baseline_value,
    extract_scoto_rod_cone_analysis,
    extract_photo_analysis,
)
from birdshot.utils.st_chart import add_fill_between
from warnings import warn
import pandas as pd
import plotly.graph_objects as go
from pickle import load
import numpy as np

from scipy import signal
import streamlit as st
from utils.colors import get_std_colors

line_dict = dict(
    width=2,
    color="#1E90FF",
)


def plot_photo(
    data,
    normal_data,
    extract_markers=False,
):
    time = data["Time (ms)"]
    labels = ["a", "b", "i"]
    markers = None
    if extract_markers:
        markers = extract_photo_analysis(data)

    col1, col2 = st.columns(2)
    for laterality, col in zip(["OD", "OS"], [col1, col2]):
        normal_values = np.asarray(
            [
                r[laterality].values
                for r in normal_data
                if len(r[laterality].values) == len(data[laterality])
            ]
        )

        mean_normal = np.mean(normal_values, axis=0)
        std_normal = np.std(normal_values, axis=0)
        fig = go.Figure()

        colors = get_std_colors()
        for std_mult, color in colors.items():
            add_fill_between(
                fig=fig,
                time=data[("Time (ms)")],
                mean_values=mean_normal,
                std_values=std_normal,
                std_mult=std_mult,
                color=color,
            )

        fig.add_trace(
            go.Line(x=time, y=data[laterality], name=laterality, line=line_dict)
        )

        fig.update_yaxes(range=[-150, 150])
        if extract_markers and markers is not None:
            for marker, label in zip(["diamond", "square", "circle"], labels):
                xpt, ypt = markers[f"{laterality} {label}"]
                fig.add_scatter(
                    x=xpt,
                    y=ypt,
                    mode="markers",
                    name=label,
                    marker=dict(size=10, symbol=marker, color="black"),
                )
        fig.update_layout(template="ggplot2")
        with col:
            st.plotly_chart(fig)


def plot_F30(
    data,
    normal_data,
    extract_markers=False,
    prominance=5,
    delta=0.7,
    filtered=180,
    align_with_normal=True,
):
    col1, col2 = st.columns(2)
    od_marker = None
    os_marker = None
    if extract_markers:
        try:
            results = extract_f30_analysis(
                data.copy(),
                filtered=filtered,
                prominance=prominance,
                delta=delta,
                plot=False,
                return_peaks=True,
                return_filtered=True,
            )
            od_marker = results[-3]
            os_marker = results[-2]
            filtered_data = results[-1]
        except Exception as e:
            warn(f"Error while extracting markers: {e}")
            filtered_data = data.copy()
    else:
        filtered_data = data.copy()

    for laterality, col, marker in zip(
        ["OD", "OS"], [col1, col2], [od_marker, os_marker]
    ):
        normal_values = np.asarray([r[1, laterality].values for r in normal_data])
        mean_normal = np.mean(normal_values, axis=0)
        std_normal = np.std(normal_values, axis=0)
        if align_with_normal:
            # Find delay between normal and filtered data by cross-correlation
            corr = signal.correlate(mean_normal, data[1, laterality], mode="full")
            lag = np.argmax(corr) - (len(mean_normal) - 1)

            # Find TE (1/Fe)
            te = data[("", "Time (ms)")][1] - data[("", "Time (ms)")][0]

            # Convert lag to time
            lag = lag * te
        else:
            lag = 0

        # Create figure
        fig = go.Figure()

        colors = get_std_colors()
        for std_mult, color in colors.items():
            add_fill_between(
                fig=fig,
                time=data[("", "Time (ms)")] - lag,
                mean_values=mean_normal,
                std_values=std_normal,
                std_mult=std_mult,
                color=color,
            )

        fig.add_trace(
            go.Line(
                x=data[("", "Time (ms)")],
                y=data[1, laterality],
                name=laterality,
                line=line_dict,
            )
        )

        # set y axis to -150 150
        fig.update_yaxes(range=[-150, 150])
        if extract_markers and marker is not None:
            fig.add_trace(
                go.Line(
                    x=filtered_data[("", "Time (ms)")],
                    y=filtered_data[1, laterality],
                    name="Filtered",
                    line=dict(color="red", width=1),
                )
            )
            for peak in marker:
                ymin, ymax, xmin, xmax = tuple(peak)
                fig.add_shape(
                    type="rect",
                    fillcolor="LightSkyBlue",
                    x0=xmin,
                    y0=ymin,
                    x1=xmax,
                    y1=ymax,
                    line=dict(color="RoyalBlue"),
                    opacity=0.5,
                    name="Peak",
                )

        with col:
            st.plotly_chart(fig)


def plot_scoto(
    data,
    normal_data,
    extract_markers=False,
    rodOnly=True,
    scotorodcone_low_pass=75,
    scotorodcone_time_limits=(10, 60),
    scotorod_low_pass=75,
    scotorod_time_limits=(10, 125),
):
    if rodOnly:
        step = 9
    else:
        step = 19

    os_markers = None
    od_markers = None
    baseline = extract_baseline_value(data.copy())

    if extract_markers:
        try:
            if rodOnly:
                amplitude, time_od, time_os, filtered = extract_scoto_rod_analysis(
                    data.copy(),
                    plot=False,
                    return_filtered=True,
                    filtered=scotorod_low_pass,
                    time_limits=scotorod_time_limits,
                )
                od_markers = [(amplitude["OD"] + baseline[(step, "OD")], time_od)]
                os_markers = [(amplitude["OS"] + baseline[(step, "OS")], time_os)]
            else:
                (
                    B_amplitude,
                    A_amplitude,
                    B_time_od,
                    A_time_od,
                    B_time_os,
                    A_time_os,
                    filtered,
                ) = extract_scoto_rod_cone_analysis(
                    data.copy(),
                    plot=False,
                    return_filtered=True,
                    filtered=scotorodcone_low_pass,
                    time_limits=scotorodcone_time_limits,
                )
                od_markers = [
                    (
                        B_amplitude["OD"] - A_amplitude["OD"] + baseline[(step, "OD")],
                        B_time_od,
                    ),
                    (-A_amplitude["OD"] + baseline[(step, "OD")], A_time_od),
                ]
                os_markers = [
                    (
                        B_amplitude["OS"] - A_amplitude["OS"] + baseline[(step, "OS")],
                        B_time_os,
                    ),
                    (-A_amplitude["OS"] + baseline[(step, "OS")], A_time_os),
                ]

        except Exception as e:
            warn(f"Error while extracting markers: {e}")

    col1, col2 = st.columns(2)
    for laterality, col, marker in zip(
        ["OD", "OS"], [col1, col2], [od_markers, os_markers]
    ):
        normal_values = [
            r[(step, laterality)] for r in normal_data if len(r) == len(data)
        ]
        mean_normal = np.mean(normal_values, axis=0)
        std_normal = np.std(normal_values, axis=0)
        fig = go.Figure()
        colors = get_std_colors()
        for std_mult, color in colors.items():
            add_fill_between(
                fig=fig,
                time=data[("", "Time (ms)")],
                mean_values=mean_normal,
                std_values=std_normal,
                std_mult=std_mult,
                color=color,
            )

        fig.add_trace(
            go.Line(
                x=data[("", "Time (ms)")],
                y=data[step, laterality],
                name=laterality,
                line=line_dict,
            )
        )

        if extract_markers and marker is not None:
            fig.add_trace(
                go.Line(
                    x=filtered[("", "Time (ms)")],
                    y=filtered[step, laterality],
                    name="Filtered",
                    line=dict(color="red", width=1),
                )
            )
            fig.add_hline(
                y=baseline[(step, laterality)],
                line_dash="dot",
                line_color="green",
                legendgroup="baseline",
                name="Baseline",
            )
            for name, m, c in zip(["B", "A"], marker, ["circle", "diamond"]):
                fig.add_scatter(
                    x=[m[1]],
                    y=[m[0]],
                    mode="markers",
                    name=name,
                    marker=dict(size=10, color="black", symbol=c),
                )
        fig.update_yaxes(range=[-250, 250])
        with col:
            st.plotly_chart(fig)
