#!/usr/bin/env python3
"""Rebuild all numerical manuscript figures from completed result summaries.

Run from the repository root with ``python analysis/plot_results.py``.
Dependencies: Python >=3.10, numpy, matplotlib. No model, GPU, PyTorch, restored
JSONL files, network connection, or handwritten result values are required.

The script reads the committed per-experiment summaries, exports the exact
plotted observations/aggregates and their source paths to analysis/figure_data,
and writes vector PDF plus 300-dpi PNG figures to paper/figures. Original
results, data, configuration, and research code are never modified.

Uncertainty conventions are deliberately distinct: the causal-access panel
uses the recorded paired-bootstrap 95% intervals; the factorial panels display
the recorded quadruplet-cluster interaction estimates and their 95% intervals;
trained-method plots
use sample standard deviation across recorded runs. The saved training traces
for selected-head adaptation repeat across seed labels, so these bars must not
be interpreted as stochastic-training robustness. Native references are read
once. These quantities are never pooled across model families.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "paper" / "figures"
FIGURE_DATA = ROOT / "analysis" / "figure_data"
INPUT_PATHS: set[str] = set()
MODELS = ("qwen3_4b", "qwen3_8b", "llama3_8b")
MODEL_NAMES = {
    "qwen3_4b": "Qwen3-4B",
    "qwen3_8b": "Qwen3-8B",
    "llama3_8b": "Llama-3.1-8B",
}
BLUE = "#1F77B4"
ORANGE = "#FF7F0E"
RED = "#D62728"
PURPLE = "#9467BD"
GRAY = "#7F7F7F"
LIGHT_GRAY = "#BDBDBD"
INK = "#111111"
GRID = "#D5D5D5"

# Reference-paper idiom: sans-serif plot labels, black axes, standard saturated
# categorical colors, light dashed grids, and conventional data marks.
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial"],
        "mathtext.fontset": "dejavusans",
        "font.size": 9,
        "axes.labelsize": 9.5,
        "axes.titlesize": 10,
        "axes.titleweight": "normal",
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.6,
        "lines.markersize": 4.3,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "axes.unicode_minus": True,
    }
)


def read_json(relative_path: str | Path) -> Any:
    path = ROOT / relative_path
    INPUT_PATHS.add(path.relative_to(ROOT).as_posix())
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def source(model: str, relative_path: str) -> str:
    return f"outputs/{model}/{relative_path}"


def unique_record(rows: list[dict[str, Any]], **criteria: Any) -> dict[str, Any]:
    matches = [row for row in rows if all(row.get(k) == v for k, v in criteria.items())]
    if len(matches) != 1:
        raise ValueError(f"Expected one row for {criteria}; found {len(matches)}")
    return matches[0]


def export_csv(name: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Empty figure-data table: {name}")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    FIGURE_DATA.mkdir(parents=True, exist_ok=True)
    with (FIGURE_DATA / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save_figure(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    # Check full-canvas text bounds before exporting at the fixed manuscript width.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    for item in fig.findobj(matplotlib.text.Text):
        if not item.get_visible() or not item.get_text():
            continue
        bounds = item.get_window_extent(renderer)
        if not np.isfinite(bounds.extents).all():
            continue
        if bounds.width > 0 and bounds.height > 0 and (
            bounds.x0 < canvas.x0 - 0.5 or bounds.x1 > canvas.x1 + 0.5
            or bounds.y0 < canvas.y0 - 0.5 or bounds.y1 > canvas.y1 + 0.5
        ):
            raise ValueError(f"Figure text extends beyond canvas: {name}: {item.get_text()}")
    # Fixed figure size is retained so 8-pt labels remain 8 pt in the manuscript.
    fig.savefig(FIGURES / f"{name}.pdf", metadata={"Creator": "CoReTrace analysis/plot_results.py"})
    fig.savefig(FIGURES / f"{name}.png", dpi=300)
    plt.close(fig)
    print(f"Wrote paper/figures/{name}.pdf and .png")


def clean_axis(ax: plt.Axes, grid_axis: str = "y", *, box: bool = False) -> None:
    ax.spines[["top", "right"]].set_visible(box)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.6, linestyle="--", alpha=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(length=3, width=0.7, pad=3)


def bars(ax: plt.Axes, x: np.ndarray, values: list[float] | np.ndarray,
         width: float, color: str, *, errors: list[float] | np.ndarray | None = None,
         label: str | None = None, labels: bool = False, decimals: int = 0,
         label_offset: float = 1.6) -> Any:
    container = ax.bar(x, values, width, color=color, edgecolor=INK, linewidth=0.45,
                       label=label, zorder=3)
    if errors is not None:
        ax.errorbar(x, values, yerr=errors, fmt="none", ecolor=INK, elinewidth=0.7,
                    capsize=2, capthick=0.7, zorder=4)
    if labels:
        for xpos, value in zip(x, values):
            ax.text(xpos, value + label_offset, f"{value:.{decimals}f}",
                    ha="center", va="bottom", fontsize=8.5, color=INK)
    return container


def mean_sd(values: list[float]) -> tuple[float, float]:
    return statistics.mean(values), statistics.stdev(values) if len(values) > 1 else 0.0


def seed_values(
    model: str,
    dataset: str,
    method: str,
    seeds: list[int],
    query: str | None = None,
) -> list[dict[str, Any]]:
    pipeline = "evaluation_fullft" if method == "fullft" else "evaluation"
    query = query or ("composed" if dataset == "core" else dataset)
    values = []
    for seed in ([seeds[0]] if method == "native" else seeds):
        filename = source(model, f"seed{seed}/{pipeline}/{dataset}/summary.json")
        stored_method = "FullFT" if method == "fullft" else method
        row = unique_record(read_json(filename)["summary"], method=stored_method, query=query)
        numerator = row["logprob_correct"] if dataset == "mmlu" else row["correct"]
        value = 100 * numerator / row["n"]
        values.append(
            {
                "model": model,
                "seed": seed,
                "method": method,
                "dataset": dataset,
                "query": query,
                "n": row["n"],
                "correct": numerator,
                "accuracy_percent": value,
                "metric": "option_probability_accuracy" if dataset == "mmlu" else "accuracy",
                "source": filename,
            }
        )
    return values


def make_diagnosis(seeds: list[int]) -> None:
    name = "data_fig3_diagnosis"
    composition, readouts, overall_readouts = [], [], []
    subpopulation_file = "analysis/internal/readout_validation.json"
    subpopulation_data = read_json(subpopulation_file)
    for model in MODELS:
        filename = source(model, f"seed{seeds[0]}/evaluation/core/summary.json")
        row = unique_record(read_json(filename)["conditional_composition"], method="native")
        denominator = row["both_constituents_correct"]
        composition.append(
            {
                "model": model,
                "total_test_sources": row["n_sources"],
                "both_constituents_correct": denominator,
                "composition_failures": row["composition_failures"],
                "composition_successes": denominator - row["composition_failures"],
                "conditional_failure_percent": 100 * row["composition_failures"] / denominator,
                "source": filename,
            }
        )
        overall_file = source(model, "native_readout/complete.json")
        diagnostic = read_json(overall_file)["diagnostics"]
        population = unique_record(subpopulation_data, directory=source(model, "native_readout"))
        subgroup = population["native_composition_failure_readout"]
        for features in ("full", "attention", "metadata"):
            row = subgroup[features]
            if row["n"] != composition[-1]["composition_failures"]:
                raise ValueError(f"Composition-failure subpopulation mismatch: {model}/{features}")
            readouts.append(
                {
                    "model": model,
                    "feature_set": features,
                    "n": row["n"],
                    "correct": row["correct"],
                    "accuracy_percent": 100 * row["correct"] / row["n"],
                    "subpopulation": "native_both_constituents_correct_composed_incorrect",
                    "source": subpopulation_file,
                    "reader_directory": source(model, "native_readout"),
                    "composition_source": filename,
                }
            )
            row = diagnostic[features]["test"]
            overall_readouts.append({"model": model, "feature_set": features, "n": row["n"],
                                     "correct": row["correct"], "accuracy_percent": 100 * row["correct"] / row["n"],
                                     "subpopulation": "all_test_sources", "source": overall_file})
    export_csv(f"{name}_composition", composition)
    export_csv(f"{name}_address_readout", readouts)
    export_csv(f"{name}_address_readout_overall", overall_readouts)

    fig, axes = plt.subplots(1, 2, figsize=(6.75, 2.72))
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.18, top=0.76, wspace=0.30)
    x = np.arange(len(MODELS))
    model_labels = [MODEL_NAMES[m] for m in MODELS]
    failures = np.array([row["conditional_failure_percent"] for row in composition])
    ax = axes[0]
    clean_axis(ax)
    width = 0.34
    bars(ax, x - width / 2, 100 - failures, width, BLUE, label="Composes", labels=True, decimals=1)
    bars(ax, x + width / 2, failures, width, ORANGE, label="Fails", labels=True, decimals=1)
    ax.set_xticks(x, model_labels)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Composition outcomes (%)")
    ax.set_title("(a) Both constituent answers correct", fontsize=9.5, pad=29)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.015), ncol=2, frameon=False,
              handlelength=1.5, columnspacing=1.5, borderaxespad=0)

    ax = axes[1]
    clean_axis(ax)
    width = 0.24
    for j, (feature_set, label, color) in enumerate([
        ("metadata", "Metadata", GRAY), ("attention", "Attention", BLUE), ("full", "Full", ORANGE)
    ]):
        values = [unique_record(readouts, model=m, feature_set=feature_set)["accuracy_percent"] for m in MODELS]
        bars(ax, x + (j - 1) * width, values, width, color, label=label,
             labels=feature_set == "full", decimals=1)
    ax.set_xticks(x, model_labels)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Bridge-address accuracy (%)")
    ax.set_title("(b) Address in failed compositions", fontsize=9.5, pad=29)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.015), ncol=3, frameon=False,
              handlelength=1.1, columnspacing=0.8, handletextpad=0.4, borderaxespad=0)
    save_figure(fig, name)


def make_causal() -> None:
    name = "data_fig4_causal"
    factors, contrasts, access = [], [], []
    for model in MODELS:
        filename = source(model, "causal_factorization/summary.json")
        data = read_json(filename)
        for row in data["summary"]:
            factors.append({"model": model, "method": row["method"], "n": row["n"],
                            "correct": row["correct"], "accuracy_percent": 100 * row["accuracy"],
                            "clusters": data["factorial_accuracy"]["clusters"], "source": filename})
        for contrast, row in data["factorial_accuracy"]["contrasts"].items():
            contrasts.append({"model": model, "contrast": contrast, "estimate_pp": 100 * row["estimate"],
                              "CI95_low_pp": 100 * row["paired_cluster_CI95"][0],
                              "CI95_high_pp": 100 * row["paired_cluster_CI95"][1],
                              "n": data["factorial_accuracy"]["n"],
                              "clusters": data["factorial_accuracy"]["clusters"], "source": filename})
        filename = source(model, "causal_access/summary.json")
        data = read_json(filename)
        for method in ("oracle_second_paragraph", "oracle_first_paragraph", "lengthmatched_other_paragraph"):
            row = unique_record(data["paired_comparisons"], method_before="native", method_after=method,
                                query="composed", metric="correct")
            access.append({"model": model, "method": method, "n": row["n"],
                           "native_correct": row["before"], "intervened_correct": row["after"],
                           "delta_pp": 100 * row["delta"],
                           "CI95_low_pp": 100 * row["paired_cluster_CI95"][0],
                           "CI95_high_pp": 100 * row["paired_cluster_CI95"][1],
                           "clusters": row["cluster_count"], "source": filename})
    export_csv(f"{name}_factorial", factors)
    export_csv(f"{name}_factorial_contrasts", contrasts)
    export_csv(f"{name}_access_controls", access)

    fig, axes = plt.subplots(2, 3, figsize=(6.75, 4.35))
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.115, top=0.855, hspace=0.66, wspace=0.32)
    width = 0.31
    for i, model in enumerate(MODELS):
        ax = axes[0, i]
        clean_axis(ax)
        receiver = [unique_record(factors, model=model, method=m)["accuracy_percent"]
                    for m in ("native", "mass_only")]
        donor = [unique_record(factors, model=model, method=m)["accuracy_percent"]
                 for m in ("conditional_only", "both")]
        bars(ax, np.arange(2) - width / 2, receiver, width, BLUE, labels=True,
             label="Receiver reading pattern")
        bars(ax, np.arange(2) + width / 2, donor, width, ORANGE, labels=True,
             label="Direct-query reading pattern")
        interaction = unique_record(contrasts, model=model, contrast="interaction")
        ax.text(0.5, 0.95,
                f"Interaction {interaction['estimate_pp']:+.0f} pp "
                f"[{interaction['CI95_low_pp']:.0f}, {interaction['CI95_high_pp']:.0f}]",
                transform=ax.transAxes, ha="center", va="top", fontsize=8.0)
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", pad=9)
        ax.set_xticks([0, 1], ["Native mass", "Calibrated"])
        ax.set_ylim(0, 105)
        ax.set_yticks([0, 25, 50, 75, 100])
        if i == 0:
            ax.set_ylabel("Composed accuracy (%)")

        ax = axes[1, i]
        clean_axis(ax)
        ax.axhline(0, color=INK, lw=0.8, zorder=2)
        controls = [("oracle_second_paragraph", "Bridge", BLUE),
                    ("oracle_first_paragraph", "Root", ORANGE),
                    ("lengthmatched_other_paragraph", "Other", GRAY)]
        for j, (method, label, color) in enumerate(controls):
            row = unique_record(access, model=model, method=method)
            value, lo, hi = row["delta_pp"], row["CI95_low_pp"], row["CI95_high_pp"]
            bars(ax, np.array([j]), [value], 0.64, color)
            ax.errorbar(j, value, yerr=np.array([[value - lo], [hi - value]]), fmt="none",
                        ecolor=INK, elinewidth=0.8, capsize=2.5, capthick=0.8, zorder=4)
            ax.text(j, hi + 1.6 if value >= 0 else lo - 1.6, f"{value:+.1f}",
                    ha="center", va="bottom" if value >= 0 else "top", fontsize=8.5)
        ax.set_title(f"({chr(100+i)}) Calibrated paragraph", pad=9, fontsize=9)
        ax.set_xticks(range(3), [label for _, label, _ in controls])
        ax.set_ylim(-30, 26)
        ax.set_yticks([-20, -10, 0, 10, 20])
        if i == 0:
            ax.set_ylabel("Accuracy change (pp)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.54, 0.995),
               ncol=2, frameon=False, handlelength=1.7, columnspacing=2.0)
    save_figure(fig, name)


def make_content(seeds: list[int]) -> None:
    name = "data_fig5_content"
    raw, aggregated = [], []
    methods = ("native", "native_budget", "body", "final")
    fields = ("original_old_correct", "edited_new_follow", "edited_old_persistence", "original_correct_then_new")
    for model in MODELS:
        for seed in seeds:
            filename = source(model, f"seed{seed}/causal_content/summary.json")
            data = read_json(filename)
            for method in methods:
                row = unique_record(data["summary"], variant=method, pool="all_sources")
                actual = unique_record(data["summary"], variant=method, pool="actual_swaps")
                for field in fields:
                    raw.append({"model": model, "seed": seed, "method": method, "metric": field,
                                "n": row["n"], "actual_swaps": actual["n"], "count": row[field],
                                "rate_percent": 100 * row[field] / row["n"], "source": filename})
        for method in methods:
            for field in fields:
                rows = [row for row in raw if row["model"] == model and row["method"] == method and row["metric"] == field]
                mean, sd = mean_sd([row["rate_percent"] for row in rows])
                # Native and mass-calibrated native use deterministic, untrained models.
                if method in {"native", "native_budget"} and sd > 1e-10:
                    raise ValueError(f"Native content references disagree across seed files: {model}/{method}")
                aggregated.append({"model": model, "method": method, "metric": field,
                                   "n_per_run": rows[0]["n"], "actual_swaps": rows[0]["actual_swaps"],
                                   "recorded_runs": 1 if method in {"native", "native_budget"} else len(rows),
                                   "mean_percent": mean, "sample_sd_percent": sd,
                                   "sources": ";".join(row["source"] for row in rows)})
    export_csv(f"{name}_seed_values", raw)
    export_csv(f"{name}_aggregated", aggregated)

    fig, axes = plt.subplots(1, 3, figsize=(6.75, 2.62), sharey=True)
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.22, top=0.76, wspace=0.25)
    metrics = [("edited_new_follow", "Edited-value\nfollowing ↑"),
               ("original_correct_then_new", "Joint\ncorrectness ↑")]
    # Preserve the full four-outcome exports above for the appendix and record
    # the exact subset shown in the main figure in a separate plot-value file.
    metric_labels = dict(metrics)
    export_csv(f"{name}_plotted", [
        {**row, "display_label": metric_labels[row["metric"]].replace("\n", " ")}
        for row in aggregated
        if row["method"] in {"native", "final"} and row["metric"] in metric_labels
    ])
    width = 0.33
    for i, (model, ax) in enumerate(zip(MODELS, axes)):
        clean_axis(ax)
        for j, (method, label, color) in enumerate([
            ("native", "Native", BLUE), ("final", "CoReTrace (Ours)", ORANGE)
        ]):
            rows = [unique_record(aggregated, model=model, method=method, metric=metric)
                    for metric, _ in metrics]
            values = [row["mean_percent"] for row in rows]
            errors = [row["sample_sd_percent"] for row in rows]
            xs = np.arange(2) + (j - 0.5) * width
            bars(ax, xs, values, width, color, errors=errors, label=label)
            for xpos, value, sd in zip(xs, values, errors):
                ax.text(xpos, value + sd + 2, f"{value:.0f}", ha="center", va="bottom", fontsize=9)
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", pad=9)
        ax.set_xticks(range(2), [label for _, label in metrics], fontsize=8.5)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100])
        if i == 0:
            ax.set_ylabel("Diagnostic questions (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.54, 0.995),
               ncol=2, frameon=False, handlelength=1.7, columnspacing=2.0)
    save_figure(fig, name)


def make_localization() -> None:
    name = "data_app_localization"
    rows, matrices, selected = [], [], []
    for model in MODELS:
        filename = source(model, "discovery/ranking.json")
        ranked = read_json(filename)["ranking"]
        selection_file = source(model, "discovery/SELECTION_FROZEN.json")
        selection = read_json(selection_file)
        active = {(int(layer), head) for layer, heads in selection["head_map"].items() for head in heads}
        n_layers = max(row["layer"] for row in ranked) + 1
        n_heads = max(row["head"] for row in ranked) + 1
        matrix = np.full((n_layers, n_heads), np.nan)
        for rank, row in enumerate(ranked, 1):
            matrix[row["layer"], row["head"]] = row["score"]
            rows.append({"model": model, "rank": rank, **row,
                         "selected": (row["layer"], row["head"]) in active,
                         "source": filename, "selection_source": selection_file})
        if np.isnan(matrix).any():
            raise ValueError(f"Incomplete all-head ranking: {model}")
        matrices.append(matrix)
        selected.append(active)
    export_csv(name, rows)
    color_max = float(max(np.abs(matrix).max() for matrix in matrices))
    norm = TwoSlopeNorm(vmin=-color_max, vcenter=0, vmax=color_max)
    fig = plt.figure(figsize=(6.75, 4.60))
    grid = fig.add_gridspec(2, 3, height_ratios=[1.9, 0.9], left=0.075, right=0.985,
                           bottom=0.11, top=0.79, hspace=0.62, wspace=0.29)
    profiles = []
    for i, (model, matrix, active) in enumerate(zip(MODELS, matrices, selected)):
        ax = fig.add_subplot(grid[0, i])
        im = ax.pcolormesh(np.arange(matrix.shape[1] + 1) - 0.5,
                           np.arange(matrix.shape[0] + 1) - 0.5, matrix,
                           cmap="RdBu_r", norm=norm, shading="flat", edgecolors="none", rasterized=False)
        ax.set_xlim(-0.5, matrix.shape[1] - 0.5)
        ax.set_ylim(matrix.shape[0] - 0.5, -0.5)
        ax.set_aspect("equal", adjustable="box", anchor="N")
        for layer, head in active:
            ax.add_patch(Rectangle((head - 0.5, layer - 0.5), 1, 1, fill=False, ec=INK, lw=0.55))
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", pad=8)
        ax.set_xticks(np.arange(0, matrix.shape[1], 8))
        ax.set_yticks(np.arange(0, matrix.shape[0], 8))
        ax.set_xlabel("Head", labelpad=2)
        ax.tick_params(length=2.5, width=0.7, pad=2)
        if i == 0:
            ax.set_ylabel("Layer")

        ax = fig.add_subplot(grid[1, i])
        clean_axis(ax, "both", box=True)
        layers = np.arange(matrix.shape[0])
        # Layer means are calculated from every head, with no smoothing or fit.
        means = matrix.mean(axis=1)
        peaks = matrix.max(axis=1)
        ax.plot(layers, means, color=BLUE, marker="o", markersize=2.6, linewidth=1.2,
                label="Mean over heads")
        ax.plot(layers, peaks, color=ORANGE, marker="s", markersize=2.3, linewidth=1.1,
                label="Maximum over heads")
        for layer, mean, peak in zip(layers, means, peaks):
            profiles.append({"model": model, "layer": int(layer), "mean_score": float(mean),
                             "maximum_score": float(peak), "heads_per_layer": matrix.shape[1],
                             "source": source(model, "discovery/ranking.json")})
        ax.axhline(0, color=GRAY, linewidth=0.6)
        ax.text(0.025, 0.94, f"({chr(100+i)})", transform=ax.transAxes, ha="left", va="top", fontsize=8.5)
        ax.set_xlim(0, matrix.shape[0] - 1)
        ax.set_xticks(np.arange(0, matrix.shape[0], 8))
        ax.set_ylim(-0.04, color_max * 1.13)
        ax.set_xlabel("Layer", labelpad=2)
        if i == 0:
            ax.set_ylabel("Attention gap")
    export_csv(f"{name}_layer_profiles", profiles)
    cax = fig.add_axes([0.16, 0.885, 0.72, 0.024])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    cb.solids.set_rasterized(False)
    cb.outline.set_linewidth(0)
    cb.ax.xaxis.set_ticks_position("top")
    cb.ax.xaxis.set_label_position("top")
    cb.set_label("Direct − composed bridge-paragraph attention", fontsize=9, labelpad=5)
    cb.ax.tick_params(labelsize=8.5, length=2, pad=2)
    fig.legend(handles=[Line2D([0], [0], color=BLUE, marker="o", markersize=3, label="Mean over heads"),
                        Line2D([0], [0], color=ORANGE, marker="s", markersize=3, label="Maximum over heads")],
               loc="center", bbox_to_anchor=(0.54, 0.332), ncol=2, frameon=False,
               handlelength=2.1, columnspacing=2.0)
    save_figure(fig, name)


def make_necessity() -> None:
    name = "data_app_necessity"
    raw = []
    query_specs = [("composed", "Composed", BLUE, "o"), ("direct_first", "First hop", BLUE, "o"),
                   ("direct_target", "Second hop", BLUE, "o")]
    measured_sizes = {}
    for model in MODELS:
        filename = source(model, "causal_necessity/summary.json")
        data = read_json(filename)
        measured_sizes[model] = sorted(int(k) for k in data["controls"])
        for query, _, _, _ in query_specs:
            base = unique_record(data["summary"], method="native", query=query)
            raw.append({"model": model, "query": query, "selection": "native", "knocked_out": 0,
                        "n": base["n"], "correct": base["correct"], "accuracy_percent": base["accuracy"]*100,
                        "source": filename})
            for selection in ["selected", "random"]:
                for size in measured_sizes[model]:
                    row = unique_record(data["summary"], method=f"{selection}_{size}", query=query)
                    raw.append({"model": model, "query": query, "selection": selection, "knocked_out": size,
                                "n": row["n"], "correct": row["correct"], "accuracy_percent": 100*row["accuracy"],
                                "random_overlap_heads": data["controls"][str(size)]["overlap_heads"], "source": filename})
    export_csv(name, raw)
    fig, axes = plt.subplots(3, 3, figsize=(6.75, 5.08), sharex=True, sharey="row")
    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.11, top=0.86, hspace=0.33, wspace=0.20)
    for col, model in enumerate(MODELS):
        selection_file = source(model, "discovery/SELECTION_FROZEN.json")
        selected_count = sum(len(heads) for heads in read_json(selection_file)["head_map"].values())
        sizes = measured_sizes[model]
        for row_index, (query, label, _, _) in enumerate(query_specs):
            ax = axes[row_index, col]
            clean_axis(ax, "both", box=True)
            ax.axvline(selected_count, color=GRAY, lw=0.8, ls="--")
            base = unique_record(raw, model=model, query=query, selection="native")["accuracy_percent"]
            for selection, linecolor, marker in [("selected", BLUE, "o"), ("random", ORANGE, "s")]:
                ys = [base] + [unique_record(raw, model=model, query=query, selection=selection,
                                            knocked_out=size)["accuracy_percent"] for size in sizes]
                ax.plot([0] + sizes, ys, color=linecolor, marker=marker, markeredgecolor="white",
                        markeredgewidth=0.4, lw=1.45, markersize=4.2, zorder=3)
                # Label the preselected intervention size; all other measured
                # points remain visible without crowding the near-zero curves.
                if row_index == 0:
                    chosen_value = unique_record(raw, model=model, query=query,
                                                  selection=selection, knocked_out=selected_count)["accuracy_percent"]
                    ax.annotate(f"{chosen_value:.1f}", (selected_count, chosen_value),
                                xytext=(0, 6), textcoords="offset points", ha="center",
                                fontsize=8.5, color=linecolor)
            ax.set_ylim(0, 45 if row_index == 0 else 100)
            ax.set_xlim(-4, 84)
            ax.set_yticks([0, 15, 30, 45] if row_index == 0 else [0, 25, 50, 75, 100])
            ax.set_xticks([0] + sizes)
            if row_index == 0:
                ax.set_title(f"({chr(97+col)}) {MODEL_NAMES[model]}", pad=8)
            if col == 0:
                ax.set_ylabel(f"{label}\nAccuracy (%)")
            if row_index == 2:
                ax.set_xlabel("Knocked-out heads")
    fig.legend(handles=[Line2D([0], [0], color=BLUE, marker="o", label="Ranked heads"),
                        Line2D([0], [0], color=ORANGE, marker="s", label="Layer-matched random heads"),
                        Line2D([0], [0], color=GRAY, ls="--", linewidth=0.8, label="Selected size")],
               loc="upper center", bbox_to_anchor=(0.54, 0.995), ncol=3, frameon=False,
               handlelength=2.3, columnspacing=2.0)
    save_figure(fig, name)


def make_ablation(seeds: list[int]) -> None:
    """Controlled effect of restoring projections outside the adapted scope.

    Core compares the same trained checkpoint and original context with only
    fixed projection restoration toggled. GSM8K has no title-delimited evidence
    paragraphs, so its recorded final path applies the same restoration alone.
    """
    name = "data_app_ablation"
    raw, aggregates = [], []
    metrics = [("direct_first", "First-hop accuracy", "core"),
               ("all3", "All-three accuracy", "core"),
               ("gsm8k", "GSM8K", "gsm8k")]
    for metric, _, dataset in metrics:
        for model in MODELS:
            for restored in (False, True):
                method = ("scoped_body" if dataset == "core" else "final") if restored else "head_tuning"
                if metric == "all3":
                    values = []
                    for seed in seeds:
                        filename = source(model, f"seed{seed}/evaluation/core/summary.json")
                        row = unique_record(read_json(filename)["all3"], method=method)
                        values.append({"model": model, "seed": seed, "method": method, "dataset": dataset,
                                       "query": metric, "n": row["n"], "correct": row["correct"],
                                       "accuracy_percent": 100 * row["correct"] / row["n"],
                                       "metric": "accuracy", "source": filename})
                else:
                    values = seed_values(model, dataset, method, seeds, query=metric)
                for row in values:
                    row["projection_restoration"] = restored
                raw.extend(values)
                mean, sd = mean_sd([row["accuracy_percent"] for row in values])
                aggregates.append({"model": model, "query": metric, "method": method,
                                   "projection_restoration": restored,
                                   "n_per_run": values[0]["n"], "runs": len(values),
                                   "mean_percent": mean, "sample_sd_percent": sd,
                                   "sources": ";".join(row["source"] for row in values)})
    export_csv(f"{name}_seed_values", raw)
    export_csv(f"{name}_aggregated", aggregates)

    fig, axes = plt.subplots(1, 3, figsize=(6.75, 2.94), sharey=True)
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.21, top=0.78, wspace=0.31)
    width = 0.32
    labels = ["Qwen3\n4B", "Qwen3\n8B", "Llama-3.1\n8B"]
    for i, (ax, (metric, metric_name, _)) in enumerate(zip(axes, metrics)):
        clean_axis(ax)
        for j, (restored, label, color) in enumerate([
            (False, "Without projection restoration", BLUE),
            (True, "With projection restoration", ORANGE)
        ]):
            rows = [unique_record(aggregates, model=m, query=metric, projection_restoration=restored)
                    for m in MODELS]
            bars(ax, np.arange(3) + (j - 0.5) * width,
                 [row["mean_percent"] for row in rows], width, color,
                 errors=[row["sample_sd_percent"] for row in rows], label=label)
        for j, model in enumerate(MODELS):
            before = unique_record(aggregates, model=model, query=metric, projection_restoration=False)
            after = unique_record(aggregates, model=model, query=metric, projection_restoration=True)
            delta = after["mean_percent"] - before["mean_percent"]
            upper = max(row["mean_percent"] + row["sample_sd_percent"] for row in [before, after])
            ax.text(j, upper + 3, f"+{delta:.1f}", ha="center", va="bottom", fontsize=8.5)
        ax.set_title(f"({chr(97+i)}) {metric_name}", pad=9)
        ax.set_xticks(range(3), labels)
        ax.set_ylim(0, 105)
        ax.set_yticks([0, 25, 50, 75, 100])
        if i == 0:
            ax.set_ylabel("Accuracy (%)")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.54, 0.995),
               ncol=2, frameon=False, handlelength=1.7, columnspacing=2.0)
    save_figure(fig, name)


def make_capabilities(seeds: list[int]) -> None:
    name = "data_app_capabilities"
    raw, aggregates = [], []
    datasets = [("hotpot", "HotpotQA", "Answer EM (%)"), ("mmlu", "MMLU", "Option accuracy (%)"),
                ("gsm8k", "GSM8K", "Numeric accuracy (%)")]
    methods = [("native", "Native", GRAY), ("fullft", "Full fine-tuning", BLUE),
               ("final", "CoReTrace (Ours)", ORANGE)]
    for dataset, _, _ in datasets:
        for model in MODELS:
            baseline = seed_values(model, dataset, "native", seeds)
            base = baseline[0]["accuracy_percent"]
            for method, _, _ in methods:
                values = baseline if method == "native" else seed_values(model, dataset, method, seeds)
                raw.extend(values)
                mean, sd = mean_sd([row["accuracy_percent"] for row in values])
                aggregates.append({"dataset": dataset, "model": model, "method": method,
                                   "n_per_run": values[0]["n"], "recorded_runs": len(values),
                                   "native_percent": base, "mean_percent": mean, "sample_sd_percent": sd,
                                   "delta_pp": mean - base, "source_native": baseline[0]["source"],
                                   "sources": ";".join(row["source"] for row in values)})
    export_csv(f"{name}_seed_values", raw)
    export_csv(f"{name}_aggregated", aggregates)

    fig, axes = plt.subplots(1, 3, figsize=(6.75, 2.94))
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.21, top=0.78, wspace=0.32)
    width = 0.24
    model_labels = ["Qwen3\n4B", "Qwen3\n8B", "Llama-3.1\n8B"]
    for i, (ax, (dataset, dataset_name, metric)) in enumerate(zip(axes, datasets)):
        clean_axis(ax)
        for j, (method, method_label, color) in enumerate(methods):
            rows = [unique_record(aggregates, dataset=dataset, model=model, method=method) for model in MODELS]
            values = [row["mean_percent"] for row in rows]
            errors = [row["sample_sd_percent"] for row in rows]
            xs = np.arange(3) + (j - 1) * width
            bars(ax, xs, values, width, color, errors=errors, label=method_label)
            if method == "fullft":
                for xpos, value in zip(xs, values):
                    if value == 0:
                        ax.text(xpos, 1.5, "0", ha="center", va="bottom", fontsize=8.5, color=BLUE, zorder=5)
            if method == "final":
                for xpos, value, sd in zip(xs, values, errors):
                    ax.text(xpos, value + sd + 2, f"{value:.1f}", ha="center", va="bottom", fontsize=8.5)
        ax.set_title(f"({chr(97+i)}) {dataset_name}", pad=9)
        ax.set_xticks(range(3), model_labels)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_ylabel(metric)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.54, 0.995),
               ncol=3, frameon=False, handlelength=1.7, columnspacing=2.0)
    save_figure(fig, name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*", choices=["diagnosis", "causal", "content", "localization", "necessity", "ablation", "capabilities"])
    args = parser.parse_args()
    config = read_json("configs/experiments.json")
    seeds = config["seeds"]
    tasks = {
        "diagnosis": lambda: make_diagnosis(seeds),
        "causal": make_causal,
        "content": lambda: make_content(seeds),
        "localization": make_localization,
        "necessity": make_necessity,
        "ablation": lambda: make_ablation(seeds),
        "capabilities": lambda: make_capabilities(seeds),
    }
    for name in args.only or tasks:
        tasks[name]()
    manifest_name = "input_manifest" if not args.only else "input_manifest_" + "_".join(args.only)
    export_csv(manifest_name, [
        {"path": path, "bytes": (ROOT / path).stat().st_size,
         "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
        for path in sorted(INPUT_PATHS)
    ])
    print(f"Read {len(INPUT_PATHS)} input files; see analysis/figure_data/{manifest_name}.csv")


if __name__ == "__main__":
    main()
