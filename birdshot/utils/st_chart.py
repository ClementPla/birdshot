import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def add_fill_between(
    fig,
    mean_values,
    std_values,
    time,
    std_mult=2.0,
    color="rgba(0,127,0,0.2)",
    showlegend=True,
):
    opacity = st.session_state.normal_opacity

    alpha = color.split(",")[-1]
    alpha = alpha[: alpha.index(")")]
    new_alpha = float(alpha) * opacity
    color = color.replace(alpha + ")", str(new_alpha) + ")")
    if st.session_state.show_norm:
        fig.add_trace(
            go.Scatter(
                x=time,
                y=mean_values - std_mult * std_values,
                name=None,
                showlegend=False,
                line=dict(color="rgba(0,0,0,0)"),
                fillcolor=color,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=time,
                y=mean_values + std_mult * std_values,
                name=f"{std_mult:.1f} SD",
                fill="tonexty",
                line=dict(color="rgba(0,0,0,0)"),
                fillcolor=color,
                showlegend=showlegend,
            )
        )
