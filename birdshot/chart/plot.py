import matplotlib.pyplot as plt
import pandas as pd
from birdshot.analysis.markers import (
    extract_baseline_value,
    extract_scoto_rod_markers,
    extract_scoto_rod_cone_markers,
)


def plot_traces(
    traces: pd.DataFrame,
    index: int | list[int] = None,
    baseline: bool = False,
    scoto_rod_markers: bool = False,
    scoto_rod_cone_markers: bool = False,
    f30_markers: bool = False,
    photo_markers: bool = False,
    ax=None,
    linewidth=1,
    fig=None,
):
    if ax is None:
        fig, ax = plt.subplots(1, 2, figsize=(15, 5), sharey=True)

        # Set ylim to -200, 200

        # ax[0].set_ylim(-175, 175)
        # ax[1].set_ylim(-175, 175)

    x = traces[("", "Time (ms)")]
    if index is not None:
        if isinstance(index, int):
            index = [index]

    all_steps = set(traces.columns.get_level_values("Step"))
    for step in all_steps:
        if step == "":
            continue

        if index is not None and step not in index:
            continue

        ax[0].plot(
            x, traces[step, "OD"], label=f"Step {step}", linewidth=linewidth, zorder=1
        )
        ax[1].plot(
            x, traces[step, "OS"], label=f"Step {step}", linewidth=linewidth, zorder=1
        )

        if baseline:
            baseline_value = extract_baseline_value(
                traces[step], traces[("", "Time (ms)")]
            )
            ax[0].axhline(
                baseline_value["OD"],
                color="red",
                linestyle="--",
                label=f"Baseline {step}",
                linewidth=1,
            )
            ax[1].axhline(
                baseline_value["OS"],
                color="red",
                linestyle="--",
                label=f"Baseline {step}",
                linewidth=1,
            )

        if scoto_rod_markers:
            ymax, xmax = extract_scoto_rod_markers(
                traces[step], traces[("", "Time (ms)")]
            )
            ax[0].scatter(
                x[xmax["OD"]],
                ymax["OD"],
                color="red",
                label=f"B ({step}) - {ymax['OD'] - baseline_value['OD']:0.2f}",
                zorder=2,
            )
            ax[1].scatter(
                x[xmax["OS"]],
                ymax["OS"],
                color="red",
                label=f"B ({step}) - {ymax['OS'] - baseline_value['OS']:0.2f}",
                zorder=2,
            )

        if scoto_rod_cone_markers:
            ymax, ymin, xmax, xmin = extract_scoto_rod_cone_markers(
                traces[step], traces[("", "Time (ms)")]
            )
            ax[0].scatter(
                x[xmax["OD"]],
                ymax["OD"],
                color="red",
                label=f"B ({step})",
                s=20,
                zorder=2,
            )
            ax[1].scatter(
                x[xmax["OS"]],
                ymax["OS"],
                color="red",
                label=f"B ({step})",
                s=20,
                zorder=2,
            )
            ax[0].scatter(
                x[xmin["OD"]],
                ymin["OD"],
                color="green",
                label=f"A ({step})",
                s=20,
                zorder=2,
            )
            ax[1].scatter(
                x[xmin["OS"]],
                ymin["OS"],
                color="green",
                label=f"A ({step})",
                s=20,
                zorder=2,
            )

        if f30_markers:
            pass

        if photo_markers:
            pass

    ax[0].set_xlabel("Time (ms)")
    ax[0].set_ylabel("Tension (uV)")

    ax[0].title.set_text("OD")
    ax[0].legend()

    ax[1].set_xlabel("Time (ms)")
    ax[1].title.set_text("OS")
    ax[1].legend()
    if fig is not None:
        return fig, ax
    else:
        return ax
