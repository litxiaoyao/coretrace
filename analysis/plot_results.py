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
the recorded quadruplet-cluster interaction intervals; trained-method plots
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
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
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
TEAL = "#087F8C"
CORAL = "#D76B50"
PURPLE = "#6F5AA8"
GRAY = "#849199"
PALE = "#E9EDEF"
PALE_TEAL = "#E5F2EF"
PALE_CORAL = "#F8ECE7"
INK = "#263239"
GRID = "#E3E6E7"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.edgecolor": GRAY,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.linewidth": 0.7,
        "lines.linewidth": 1.5,
        "lines.markersize": 4,
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


def clean_axis(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.55, linestyle=(0, (2, 2)))
    ax.set_axisbelow(True)
    ax.tick_params(length=2.5, width=0.6)


def highlight_row(ax: plt.Axes, row: float, height: float = 0.82) -> None:
    """A shared, understated background identifies our complete intervention."""
    ax.axhspan(row - height / 2, row + height / 2, color=PALE_TEAL, lw=0, zorder=0)


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

    fig, axes = plt.subplots(1, 2, figsize=(6.75, 2.38), gridspec_kw={"width_ratios": [1, 1.08]})
    fig.subplots_adjust(left=0.15, right=0.975, bottom=0.21, top=0.72, wspace=0.26)
    y = np.arange(len(MODELS))
    failures = np.array([row["conditional_failure_percent"] for row in composition])
    successes = 100 - failures
    ax = axes[0]
    clean_axis(ax, "x")
    ax.barh(y, successes, height=0.56, color=TEAL, edgecolor="white", linewidth=0.5)
    ax.barh(y, failures, left=successes, height=0.56, color=CORAL, edgecolor="white", linewidth=0.5)
    for i, (succ, fail) in enumerate(zip(successes, failures)):
        ax.text(succ / 2, i, f"{succ:.1f}", ha="center", va="center", color="white", fontsize=9)
        ax.text(succ + fail / 2, i, f"{fail:.1f}", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    ax.set_yticks(y, [f"{MODEL_NAMES[m]}\n$n$ = {composition[i]['both_constituents_correct']}" for i, m in enumerate(MODELS)])
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_ylim(2.6, -0.6)
    ax.set_xlabel("Composition outcomes (%)")
    ax.set_title("(a) Both constituent answers correct", loc="left", pad=30)
    ax.legend(handles=[Patch(color=TEAL, label="Composes"), Patch(color=CORAL, label="Fails")],
              loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2, frameon=False,
              handlelength=1.1, columnspacing=1.1, borderaxespad=0)

    ax = axes[1]
    clean_axis(ax, "x")
    features = [("metadata", "Metadata", GRAY, "s", 0.16),
                ("attention", "Attention", PURPLE, "D", 0),
                ("full", "Full", TEAL, "o", -0.16)]
    for feature_set, label, color, marker, offset in features:
        xs = [unique_record(readouts, model=m, feature_set=feature_set)["accuracy_percent"] for m in MODELS]
        ax.scatter(xs, y + offset, color=color, marker=marker, s=25 if feature_set == "full" else 20,
                   label=label, zorder=3, linewidths=0.5, edgecolors="white")
        if feature_set != "attention":
            for xpos, ypos in zip(xs, y + offset):
                ax.text(xpos + 3, ypos, f"{xpos:.1f}", va="center", ha="left", color=color,
                        fontsize=9, fontweight="bold" if feature_set == "full" else "normal")
    for i, row in enumerate(composition):
        ax.text(1.5, i, f"$n$ = {row['composition_failures']}", ha="left", va="center", color=GRAY, fontsize=8.5)
    ax.set_yticks(y, [])
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 105)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_ylim(2.6, -0.6)
    ax.set_xlabel("Bridge-address accuracy (%)")
    ax.set_title("(b) Address in failed compositions", loc="left", pad=30)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=3,
              frameon=False, handletextpad=0.3, columnspacing=0.9, borderaxespad=0)
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

    fig = plt.figure(figsize=(6.75, 3.92))
    grid = fig.add_gridspec(2, 3, height_ratios=[1.07, 1], left=0.085, right=0.97,
                           top=0.85, bottom=0.12, hspace=0.98, wspace=0.35)
    line_handles = []
    for i, model in enumerate(MODELS):
        ax = fig.add_subplot(grid[0, i])
        clean_axis(ax)
        receiver = [unique_record(factors, model=model, method=m)["accuracy_percent"] for m in ("native", "mass_only")]
        donor = [unique_record(factors, model=model, method=m)["accuracy_percent"] for m in ("conditional_only", "both")]
        line1, = ax.plot([0, 1], receiver, color=PURPLE, marker="o", label="Receiver reading pattern", markersize=4.5)
        line2, = ax.plot([0, 1], donor, color=TEAL, marker="D", label="Direct-query reading pattern", markersize=4.5)
        if i == 0:
            line_handles = [line1, line2]
        for index, values in enumerate((receiver, donor)):
            other = donor if index == 0 else receiver
            for xpos, value in enumerate(values):
                is_upper = value >= other[xpos]
                ax.annotate(f"{value:.0f}", (xpos, value), xytext=(0, 8 if is_upper else -8),
                            textcoords="offset points", ha="center", va="center", fontsize=9,
                            color=PURPLE if index == 0 else TEAL)
        interaction = unique_record(contrasts, model=model, contrast="interaction")
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", loc="left", pad=19)
        ax.text(0.5, 1.035,
                f"Interaction {interaction['estimate_pp']:+.0f} [{interaction['CI95_low_pp']:.0f}, {interaction['CI95_high_pp']:.0f}] pp",
                transform=ax.transAxes, ha="center", va="bottom", fontsize=9, color=TEAL)
        ax.set_xlim(-0.2, 1.2)
        ax.set_xticks([0, 1], ["Native mass", "Calibrated"])
        ax.set_ylim(15, 88)
        ax.set_yticks([20, 40, 60, 80])
        if i == 0:
            ax.set_ylabel("Composed accuracy (%)")
    fig.legend(handles=line_handles, loc="upper center", bbox_to_anchor=(0.53, 1.005),
               ncol=2, frameon=False, handlelength=2.0, columnspacing=1.8)

    ax = fig.add_subplot(grid[1, :])
    lower = ax.get_position()
    ax.set_position([0.15, lower.y0, 0.82, lower.height])
    clean_axis(ax, "x")
    ax.axvline(0, color=GRAY, lw=0.8)
    methods = [("oracle_second_paragraph", "Bridge paragraph", TEAL, "o", -0.3),
               ("oracle_first_paragraph", "First-hop paragraph", PURPLE, "D", 0),
               ("lengthmatched_other_paragraph", "Length-matched other", GRAY, "s", 0.3)]
    for method, label, color, marker, offset in methods:
        rows = [unique_record(access, model=model, method=method) for model in MODELS]
        xs = np.array([row["delta_pp"] for row in rows])
        lo = np.array([row["CI95_low_pp"] for row in rows])
        hi = np.array([row["CI95_high_pp"] for row in rows])
        positions = np.arange(3) + offset
        ax.errorbar(xs, positions, xerr=np.array([xs - lo, hi - xs]), fmt=marker, color=color,
                    markeredgecolor="white", markeredgewidth=0.4, markersize=4.5,
                    capsize=2, elinewidth=1, capthick=0.8, label=label)
        for value, ypos, lower, upper in zip(xs, positions, lo, hi):
            xpos = upper + 0.8 if value >= 0 else lower - 0.8
            ax.text(xpos, ypos, f"{value:+.1f}", ha="left" if value >= 0 else "right",
                    va="center", fontsize=9, color=color,
                    fontweight="bold" if method == "oracle_second_paragraph" else "normal")
    ax.set_title("(d) Address-specific calibration on the complete test set", loc="left", pad=26)
    ax.legend(loc="lower center", bbox_to_anchor=(0.52, 1.025), ncol=3, frameon=False,
              handlelength=1.4, columnspacing=1.8, borderaxespad=0)
    ax.set_yticks(np.arange(3), [MODEL_NAMES[m] for m in MODELS])
    ax.tick_params(axis="y", labelsize=9)
    ax.set_ylim(2.6, -0.6)
    ax.set_xlim(-30, 25)
    ax.set_xticks([-20, -10, 0, 10, 20])
    ax.set_xlabel("Composed-accuracy change (percentage points)")
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

    fig, axes = plt.subplots(1, 3, figsize=(6.75, 2.6), sharey=True)
    fig.subplots_adjust(left=0.165, right=0.98, bottom=0.22, top=0.76, wspace=0.21)
    y = np.arange(len(methods))
    method_labels = ["Native", "Mass calibration", "Scoped adaptation", "CoReTrace (Ours)"]
    for i, (model, ax) in enumerate(zip(MODELS, axes)):
        clean_axis(ax, "x")
        highlight_row(ax, 3)
        for metric, label, color, marker, offset in [
            ("edited_new_follow", "Follows edited value", TEAL, "o", -0.13),
            ("edited_old_persistence", "Keeps obsolete answer", CORAL, "s", 0.13),
        ]:
            rows = [unique_record(aggregated, model=model, method=method, metric=metric) for method in methods]
            xs = [row["mean_percent"] for row in rows]
            sds = [row["sample_sd_percent"] for row in rows]
            ax.errorbar(xs, y + offset, xerr=sds, fmt=marker, color=color, markersize=4.6,
                        markeredgecolor="white", markeredgewidth=0.45,
                        capsize=2, elinewidth=0.8, label=label, zorder=3)
            for xpos, ypos, sd in zip(xs, y + offset, sds):
                ax.text(xpos + sd + 3.3, ypos, f"{xpos:.0f}", ha="left", va="center", fontsize=9, color=color)
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", loc="left", pad=8)
        ax.set_yticks(y, method_labels)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_ylim(3.55, -0.55)
        ax.set_xlabel("Diagnostic questions (%)")
        for label in ax.get_yticklabels():
            if label.get_text().startswith("CoReTrace"):
                label.set_fontweight("bold")
                label.set_color(TEAL)
    fig.legend(handles=[Line2D([0], [0], color=TEAL, marker="o", ls="", label="Follows edited value"),
                        Line2D([0], [0], color=CORAL, marker="s", ls="", label="Keeps obsolete answer")],
               loc="upper center", bbox_to_anchor=(0.56, 1.0), ncol=2, frameon=False,
               columnspacing=2, handletextpad=0.5)
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
    cmap = LinearSegmentedColormap.from_list("paragraph_gap", [CORAL, "#FFFFFF", TEAL])
    norm = TwoSlopeNorm(vmin=-color_max, vcenter=0, vmax=color_max)
    fig, axes = plt.subplots(1, 3, figsize=(6.75, 3.18))
    fig.subplots_adjust(left=0.065, right=0.985, bottom=0.32, top=0.84, wspace=0.23)
    for i, (model, matrix, active, ax) in enumerate(zip(MODELS, matrices, selected, axes)):
        im = ax.pcolormesh(np.arange(matrix.shape[1] + 1) - 0.5,
                           np.arange(matrix.shape[0] + 1) - 0.5, matrix,
                           cmap=cmap, norm=norm, shading="flat", edgecolors="none", rasterized=False)
        ax.set_xlim(-0.5, matrix.shape[1] - 0.5)
        ax.set_ylim(matrix.shape[0] - 0.5, -0.5)
        for layer, head in active:
            ax.add_patch(Rectangle((head - 0.5, layer - 0.5), 1, 1, fill=False, ec=INK, lw=0.65))
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", loc="left", pad=22)
        ax.text(0.5, 1.025, f"{len(active)} selected heads", transform=ax.transAxes,
                ha="center", va="bottom", color=TEAL, fontsize=9)
        ax.set_xticks(sorted(set([0, 8, 16, 24, matrix.shape[1] - 1])))
        ax.set_yticks(sorted(set([0, 8, 16, 24, matrix.shape[0] - 1])))
        ax.set_xlabel("Head index")
        ax.tick_params(length=2, width=0.6)
        if i == 0:
            ax.set_ylabel("Layer index")
    cax = fig.add_axes([0.29, 0.12, 0.46, 0.035])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    cb.solids.set_rasterized(False)
    cb.outline.set_linewidth(0.5)
    cb.set_label("Direct − composed bridge-paragraph attention", fontsize=9, labelpad=2)
    cb.ax.tick_params(labelsize=8.5, length=2, pad=2)
    save_figure(fig, name)


def make_necessity() -> None:
    name = "data_app_necessity"
    raw = []
    query_specs = [("composed", "Composed", TEAL, "o"), ("direct_first", "First hop", CORAL, "^"),
                   ("direct_target", "Second hop", PURPLE, "D")]
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
    fig, axes = plt.subplots(3, 3, figsize=(6.75, 5.0), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.105, top=0.86, hspace=0.36, wspace=0.20)
    for col, model in enumerate(MODELS):
        selection_file = source(model, "discovery/SELECTION_FROZEN.json")
        selected_count = sum(len(heads) for heads in read_json(selection_file)["head_map"].values())
        sizes = measured_sizes[model]
        for row_index, (query, label, color, marker) in enumerate(query_specs):
            ax = axes[row_index, col]
            clean_axis(ax)
            ax.axvline(selected_count, color=GRID, lw=0.8, ls=":")
            base = unique_record(raw, model=model, query=query, selection="native")["accuracy_percent"]
            for selection, linestyle, linecolor in [("selected", "-", color), ("random", "--", GRAY)]:
                ys = [base] + [unique_record(raw, model=model, query=query, selection=selection,
                                            knocked_out=size)["accuracy_percent"] for size in sizes]
                ax.plot([0] + sizes, ys, color=linecolor, marker=marker if selection == "selected" else "o",
                        ls=linestyle, lw=1.35, markersize=3.8 if selection == "selected" else 3.2)
            ax.set_ylim(0, 100)
            ax.set_xlim(-4, 84)
            ax.set_yticks([0, 50, 100])
            ax.set_xticks([0] + sizes)
            if row_index == 0:
                ax.set_title(f"({chr(97+col)}) {MODEL_NAMES[model]}", loc="left", pad=8)
                chosen = unique_record(raw, model=model, query=query, selection="selected", knocked_out=selected_count)
                random = unique_record(raw, model=model, query=query, selection="random", knocked_out=selected_count)
                ax.text(0.98, 0.92, f"Top {selected_count}: {chosen['accuracy_percent']:.1f}%\nRandom: {random['accuracy_percent']:.1f}%",
                        ha="right", va="top", transform=ax.transAxes, fontsize=8.5,
                        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1})
            if col == 0:
                ax.set_ylabel(f"{label}\nAccuracy (%)")
            if row_index == 2:
                ax.set_xlabel("Knocked-out heads")
    fig.legend(handles=[Line2D([0], [0], color=INK, marker="o", ls="-", label="Ranked-head knockout"),
                        Line2D([0], [0], color=GRAY, marker="o", ls="--", label="Layer-matched random knockout")],
               loc="upper center", bbox_to_anchor=(0.54, 0.995), ncol=2, frameon=False,
               handlelength=2.3, columnspacing=2)
    save_figure(fig, name)


def make_ablation(seeds: list[int]) -> None:
    name = "data_app_ablation"
    methods = [
        ("native", "Native", GRAY),
        ("fullft", "Full fine-tuning", CORAL),
        ("native_text", "Evidence filtering", GRAY),
        ("head_tuning", "Head tuning", PURPLE),
        ("scoped_body", "Scoped adaptation", PURPLE),
        ("graphfirst", "Graph-first selection", CORAL),
        ("final_metadata", "Metadata-only reader", GRAY),
        ("final_attention", "Attention-only reader", TEAL),
        ("final", "CoReTrace (Ours)", TEAL),
    ]
    raw, aggregates = [], []
    for model in MODELS:
        for method, _, _ in methods:
            values = seed_values(model, "core", method, seeds)
            raw.extend(values)
            mean, sd = mean_sd([row["accuracy_percent"] for row in values])
            aggregates.append({"model": model, "method": method, "n_per_run": values[0]["n"],
                               "runs": len(values), "mean_percent": mean, "sample_sd_percent": sd,
                               "sources": ";".join(row["source"] for row in values)})
    export_csv(f"{name}_seed_values", raw)
    export_csv(f"{name}_aggregated", aggregates)

    fig, axes = plt.subplots(1, 3, figsize=(6.75, 3.15), sharey=True)
    fig.subplots_adjust(left=0.22, right=0.985, bottom=0.14, top=0.84, wspace=0.20)
    y = np.arange(len(methods))
    for i, (model, ax) in enumerate(zip(MODELS, axes)):
        clean_axis(ax, "x")
        baseline = unique_record(aggregates, model=model, method="native")["mean_percent"]
        final = unique_record(aggregates, model=model, method="final")["mean_percent"]
        highlight_row(ax, len(methods) - 1)
        ax.axvline(baseline, color=GRAY, ls=":", lw=0.9)
        for j, (method, label, color) in enumerate(methods):
            row = unique_record(aggregates, model=model, method=method)
            mean, sd = row["mean_percent"], row["sample_sd_percent"]
            ax.errorbar(mean, j, xerr=sd, color=color, marker="D" if method == "final" else "o",
                        markeredgecolor="white", markeredgewidth=0.4,
                        markersize=6 if method == "final" else 4.5,
                        capsize=2, elinewidth=0.8, zorder=3)
            ax.text(mean + sd + 3.5, j, f"{mean:.1f}", ha="left", va="center", fontsize=9,
                    fontweight="bold" if method == "final" else "normal",
                    color=TEAL if method == "final" else INK)
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", loc="left", pad=23)
        ax.text(0.5, 1.02, f"Ours − Native: +{final - baseline:.1f} pp", transform=ax.transAxes,
                ha="center", va="bottom", color=TEAL, fontsize=9)
        ax.set_xlim(0, 90)
        ax.set_xticks([0, 20, 40, 60, 80])
        ax.set_xlabel("Composed accuracy (%)")
        ax.set_yticks(y, [label for _, label, _ in methods])
        ax.set_ylim(len(methods) - 0.4, -0.6)
        ax.axhline(2.5, color=GRID, lw=0.8)
        ax.axhline(5.5, color=GRID, lw=0.8)
        for label in ax.get_yticklabels():
            if label.get_text().startswith("CoReTrace"):
                label.set_fontweight("bold")
                label.set_color(TEAL)
    save_figure(fig, name)


def make_capabilities(seeds: list[int]) -> None:
    name = "data_app_capabilities"
    raw, aggregates = [], []
    datasets = [("hotpot", "HotpotQA", "Answer EM"), ("mmlu", "MMLU", "Option accuracy"),
                ("gsm8k", "GSM8K", "Numeric accuracy")]
    methods = [("head_tuning", "Head tuning", PURPLE), ("fullft", "Full fine-tuning", CORAL),
               ("final", "CoReTrace", TEAL)]
    for dataset, _, _ in datasets:
        for model in MODELS:
            baseline = seed_values(model, dataset, "native", seeds)
            raw.extend(baseline)
            base = baseline[0]["accuracy_percent"]
            for method, _, _ in methods:
                values = seed_values(model, dataset, method, seeds)
                raw.extend(values)
                mean, sd = mean_sd([row["accuracy_percent"] for row in values])
                aggregates.append({"dataset": dataset, "model": model, "method": method,
                                   "n_per_run": values[0]["n"], "recorded_runs": len(values),
                                   "native_percent": base, "mean_percent": mean, "sample_sd_percent": sd,
                                   "delta_pp": mean - base, "source_native": baseline[0]["source"],
                                   "sources": ";".join(row["source"] for row in values)})
    export_csv(f"{name}_seed_values", raw)
    export_csv(f"{name}_aggregated", aggregates)

    fig, axes = plt.subplots(3, 3, figsize=(6.75, 5.0), sharex=True)
    fig.subplots_adjust(left=0.16, right=0.985, bottom=0.08, top=0.90, hspace=0.45, wspace=0.20)
    method_order = [("native", "Native", GRAY), ("fullft", "Full fine-tuning", CORAL),
                    ("head_tuning", "Head tuning", PURPLE), ("final", "CoReTrace (Ours)", TEAL)]
    for row_index, (dataset, dataset_name, metric) in enumerate(datasets):
        for col, model in enumerate(MODELS):
            ax = axes[row_index, col]
            clean_axis(ax, "x")
            highlight_row(ax, 3)
            baseline = unique_record(aggregates, dataset=dataset, model=model, method="final")["native_percent"]
            for j, (method, method_label, color) in enumerate(method_order):
                if method == "native":
                    value, sd = baseline, 0.0
                else:
                    item = unique_record(aggregates, dataset=dataset, model=model, method=method)
                    value, sd = item["mean_percent"], item["sample_sd_percent"]
                ax.barh(j, value, height=0.50, color=color, alpha=0.95,
                        edgecolor="white", linewidth=0.4, zorder=2)
                ax.errorbar(value, j, xerr=sd, fmt="none", color=INK, elinewidth=0.7,
                            capsize=1.8, capthick=0.7, zorder=3)
                ax.text(value - 3 if value >= 24 else value + sd + 3, j, f"{value:.1f}",
                        ha="right" if value >= 24 else "left", va="center", fontsize=9,
                        color="white" if value >= 24 else color,
                        fontweight="bold" if method == "final" else "normal")
            delta = unique_record(aggregates, dataset=dataset, model=model, method="final")["delta_pp"]
            ax.text(0.98, 1.025, f"Ours − Native: {delta:+.1f} pp", transform=ax.transAxes,
                    ha="right", va="bottom", fontsize=8.5, color=TEAL if delta >= 0 else CORAL)
            if row_index == 0:
                ax.set_title(MODEL_NAMES[model], loc="center", pad=22)
            ax.set_xlim(0, 100)
            ax.set_xticks([0, 25, 50, 75, 100])
            ax.set_ylim(3.65, -0.55)
            ax.set_yticks(range(4), [label for _, label, _ in method_order] if col == 0 else [])
            ax.tick_params(axis="y", length=0)
            if col == 0:
                fig.text(0.01, ax.get_position().y1 + 0.009, f"({chr(97+row_index)}) {dataset_name}",
                         ha="left", va="bottom", fontsize=10, fontweight="bold")
                for label in ax.get_yticklabels():
                    if label.get_text().startswith("CoReTrace"):
                        label.set_fontweight("bold")
                        label.set_color(TEAL)
            if row_index == 2:
                ax.set_xlabel("Accuracy (%)")
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
