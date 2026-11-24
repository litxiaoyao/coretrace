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
INK = "#263239"
GRID = "#E2E7E9"

plt.rcParams.update(
    {
        "font.family": "DejaVu Serif",
        "mathtext.fontset": "dejavuserif",
        "font.size": 8.5,
        "axes.labelsize": 8.5,
        "axes.titlesize": 9,
        "axes.titleweight": "bold",
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
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
    # Fixed figure size is retained so 8-pt labels remain 8 pt in the manuscript.
    fig.savefig(FIGURES / f"{name}.pdf", metadata={"Creator": "CoReTrace analysis/plot_results.py"})
    fig.savefig(FIGURES / f"{name}.png", dpi=300)
    plt.close(fig)
    print(f"Wrote paper/figures/{name}.pdf and .png")


def clean_axis(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=2.5, width=0.6)


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

    fig, axes = plt.subplots(1, 2, figsize=(6.75, 2.48), gridspec_kw={"width_ratios": [1, 1.12]})
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.22, top=0.72, wspace=0.34)
    x = np.arange(len(MODELS))
    failures = np.array([row["conditional_failure_percent"] for row in composition])
    successes = 100 - failures
    ax = axes[0]
    clean_axis(ax)
    ax.bar(x, successes, width=0.56, color=TEAL, edgecolor="white", linewidth=0.5)
    ax.bar(x, failures, bottom=successes, width=0.56, color=CORAL, edgecolor="white", linewidth=0.5)
    for i, (succ, fail) in enumerate(zip(successes, failures)):
        ax.text(i, succ / 2, f"{succ:.1f}", ha="center", va="center", color="white", fontsize=8.5)
        ax.text(i, succ + fail / 2, f"{fail:.1f}", ha="center", va="center", color="white", fontsize=8.5)
    ax.set_xticks(x, [f"{MODEL_NAMES[m]}\n$n$={composition[i]['both_constituents_correct']}" for i, m in enumerate(MODELS)])
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Conditional composition (%)")
    ax.set_title("(a) Both constituent answers are correct", loc="left", pad=31)
    ax.legend(handles=[Patch(color=TEAL, label="Composes"), Patch(color=CORAL, label="Fails")],
              loc="lower center", bbox_to_anchor=(0.5, 1.025), ncol=2, frameon=False,
              handlelength=1.1, columnspacing=1.1, borderaxespad=0)

    ax = axes[1]
    clean_axis(ax)
    width = 0.27
    features = [("full", "Full", TEAL), ("attention", "Attention", PURPLE), ("metadata", "Metadata", GRAY)]
    for j, (feature_set, label, color) in enumerate(features):
        ys = [unique_record(readouts, model=m, feature_set=feature_set)["accuracy_percent"] for m in MODELS]
        positions = x + (j - 1) * width
        ax.bar(positions, ys, width=width, color=color, edgecolor="white", linewidth=0.4, label=label)
        for pos, value in zip(positions, ys):
            # Stagger adjacent labels so nearly equal full/attention bars stay legible.
            ax.text(pos, value - 9 if feature_set == "attention" else value + 2,
                    f"{value:.1f}", ha="center", va="bottom", fontsize=8,
                    color="white" if feature_set == "attention" else INK)
    ax.set_xticks(x, [f"{MODEL_NAMES[m]}\n$n$={composition[i]['composition_failures']}" for i, m in enumerate(MODELS)])
    ax.set_ylim(0, 106)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Bridge-address accuracy (%)")
    ax.set_title("(b) Address in failed compositions", loc="left", pad=31)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.025), ncol=3, frameon=False,
              handlelength=1.0, columnspacing=0.8, borderaxespad=0)
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

    fig = plt.figure(figsize=(6.75, 4.22))
    grid = fig.add_gridspec(2, 3, height_ratios=[1.13, 1], left=0.09, right=0.985,
                           top=0.83, bottom=0.10, hspace=0.75, wspace=0.32)
    line_handles = []
    for i, model in enumerate(MODELS):
        ax = fig.add_subplot(grid[0, i])
        clean_axis(ax)
        receiver = [unique_record(factors, model=model, method=m)["accuracy_percent"] for m in ("native", "mass_only")]
        donor = [unique_record(factors, model=model, method=m)["accuracy_percent"] for m in ("conditional_only", "both")]
        line1, = ax.plot([0, 1], receiver, color=TEAL, marker="o", label="Receiver conditional pattern")
        line2, = ax.plot([0, 1], donor, color=CORAL, marker="D", label="Direct-query conditional pattern")
        if i == 0:
            line_handles = [line1, line2]
        for index, values in enumerate((receiver, donor)):
            other = donor if index == 0 else receiver
            for x, value in enumerate(values):
                is_upper = value >= other[x]
                ax.annotate(f"{value:.0f}", (x, value), xytext=(0, 7 if is_upper else -6),
                            textcoords="offset points", ha="center", va="center", fontsize=8.5)
        interaction = unique_record(contrasts, model=model, contrast="interaction")
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", loc="left", pad=19)
        ax.text(0.5, 1.035,
                f"Interaction {interaction['estimate_pp']:+.0f} [{interaction['CI95_low_pp']:.0f}, {interaction['CI95_high_pp']:.0f}] pp",
                transform=ax.transAxes, ha="center", va="bottom", fontsize=8)
        ax.set_xlim(-0.25, 1.30)
        ax.set_xticks([0, 1], ["Native\nmass", "Calibrated\nmass"])
        ax.set_ylim(20, 86)
        ax.set_yticks([20, 40, 60, 80])
        if i == 0:
            ax.set_ylabel("Composed accuracy (%)")
    fig.legend(handles=line_handles, loc="upper center", bbox_to_anchor=(0.53, 0.997),
               ncol=2, frameon=False, handlelength=2.0, columnspacing=1.7)

    ax = fig.add_subplot(grid[1, :])
    clean_axis(ax)
    ax.axhline(0, color=GRAY, lw=0.8)
    groups = np.arange(3)
    width = 0.22
    methods = [("oracle_second_paragraph", "Bridge paragraph", TEAL),
               ("oracle_first_paragraph", "First-hop paragraph", PURPLE),
               ("lengthmatched_other_paragraph", "Length-matched other", GRAY)]
    for j, (method, label, color) in enumerate(methods):
        rows = [unique_record(access, model=model, method=method) for model in MODELS]
        ys = np.array([row["delta_pp"] for row in rows])
        lo = np.array([row["CI95_low_pp"] for row in rows])
        hi = np.array([row["CI95_high_pp"] for row in rows])
        positions = groups + (j - 1) * width
        ax.bar(positions, ys, width=width, color=color, edgecolor="white", lw=0.5, label=label)
        ax.errorbar(positions, ys, yerr=np.array([ys - lo, hi - ys]), fmt="none", ecolor=INK,
                    capsize=2, elinewidth=0.8, capthick=0.8)
        for pos, value, lower, upper in zip(positions, ys, lo, hi):
            ax.text(pos, upper + 1.1 if value >= 0 else lower - 1.1, f"{value:+.1f}",
                    ha="center", va="bottom" if value >= 0 else "top", fontsize=8)
    ax.set_title("(d) Calibrating the addressed paragraph on the full test set", loc="left", pad=26)
    ax.legend(loc="lower center", bbox_to_anchor=(0.52, 1.025), ncol=3, frameon=False,
              handlelength=1.2, columnspacing=1.8, borderaxespad=0)
    ax.set_xticks(groups, [MODEL_NAMES[m] for m in MODELS])
    ax.set_ylim(-29, 24)
    ax.set_yticks([-20, 0, 20])
    ax.set_ylabel("Accuracy change (pp)")
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

    fig, axes = plt.subplots(1, 3, figsize=(6.75, 2.58), sharey=True)
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.24, top=0.77, wspace=0.20)
    # Leave room for the full method name while keeping the three model panels compact.
    x = np.array([0.0, 1.0, 2.05, 3.65])
    width = 0.34
    for i, (model, ax) in enumerate(zip(MODELS, axes)):
        clean_axis(ax)
        for j, (metric, label, color) in enumerate([
            ("edited_new_follow", "Follows edited value", TEAL),
            ("edited_old_persistence", "Keeps obsolete answer", CORAL),
        ]):
            rows = [unique_record(aggregated, model=model, method=method, metric=metric) for method in methods]
            ys = [row["mean_percent"] for row in rows]
            sds = [row["sample_sd_percent"] for row in rows]
            positions = x + (j - 0.5) * width
            ax.bar(positions, ys, width, color=color, edgecolor="white", linewidth=0.4, label=label)
            ax.errorbar(positions, ys, yerr=sds, fmt="none", ecolor=INK, capsize=2, elinewidth=0.7)
            for pos, value, sd in zip(positions, ys, sds):
                ax.text(pos, value + sd + 1.8, f"{value:.0f}" if abs(value-round(value)) < 1e-8 else f"{value:.1f}",
                        ha="center", va="bottom", fontsize=8)
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", loc="left", pad=7)
        ax.set_xticks(x, ["Native", "Mass\ncalib.", "Scoped\nadapt.", "CoReTrace"])
        ax.set_xlim(-0.55, 4.50)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100])
    axes[0].set_ylabel("Share of original sources (%)")
    fig.legend(handles=[Patch(color=TEAL, label="Follows edited value"), Patch(color=CORAL, label="Keeps obsolete answer")],
               loc="upper center", bbox_to_anchor=(0.53, 0.99), ncol=2, frameon=False, columnspacing=2)
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
    cmap = LinearSegmentedColormap.from_list("paragraph_gap", [PURPLE, "#FAFAF7", TEAL])
    norm = TwoSlopeNorm(vmin=-color_max, vcenter=0, vmax=color_max)
    fig, axes = plt.subplots(1, 3, figsize=(6.75, 2.82))
    fig.subplots_adjust(left=0.065, right=0.88, bottom=0.19, top=0.83, wspace=0.26)
    for i, (model, matrix, active, ax) in enumerate(zip(MODELS, matrices, selected, axes)):
        im = ax.pcolormesh(np.arange(matrix.shape[1] + 1) - 0.5,
                           np.arange(matrix.shape[0] + 1) - 0.5, matrix,
                           cmap=cmap, norm=norm, shading="flat", edgecolors="none", rasterized=False)
        ax.set_xlim(-0.5, matrix.shape[1] - 0.5)
        ax.set_ylim(matrix.shape[0] - 0.5, -0.5)
        for layer, head in active:
            ax.add_patch(Rectangle((head - 0.5, layer - 0.5), 1, 1, fill=False, ec=INK, lw=0.55))
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}\n{len(active)} selected heads", loc="left", pad=7)
        ax.set_xticks([0, 8, 16, 24, matrix.shape[1] - 1])
        ax.set_yticks(sorted(set([0, 8, 16, 24, matrix.shape[0] - 1])))
        ax.set_xlabel("Head index")
        ax.tick_params(length=2, width=0.6)
        if i == 0:
            ax.set_ylabel("Layer index")
    cax = fig.add_axes([0.905, 0.19, 0.018, 0.64])
    cb = fig.colorbar(im, cax=cax)
    cb.solids.set_rasterized(False)
    cb.set_label("Direct − composed paragraph mass", fontsize=8)
    cb.ax.tick_params(labelsize=8, length=2)
    save_figure(fig, name)


def make_necessity() -> None:
    name = "data_app_necessity"
    raw = []
    fig, axes = plt.subplots(1, 3, figsize=(6.75, 2.97), sharey=True)
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.18, top=0.70, wspace=0.22)
    query_specs = [("composed", "Composed", TEAL, "o"), ("direct_first", "First hop", CORAL, "^"),
                   ("direct_target", "Target hop", PURPLE, "D")]
    for i, (model, ax) in enumerate(zip(MODELS, axes)):
        filename = source(model, "causal_necessity/summary.json")
        data = read_json(filename)
        sizes = sorted(int(k) for k in data["controls"])
        clean_axis(ax)
        for query, label, color, marker in query_specs:
            base = unique_record(data["summary"], method="native", query=query)
            raw.append({"model": model, "query": query, "selection": "native", "knocked_out": 0,
                        "n": base["n"], "correct": base["correct"], "accuracy_percent": base["accuracy"]*100,
                        "source": filename})
            for selection, style in [("selected", "-"), ("random", "--")]:
                ys = [base["accuracy"] * 100]
                for size in sizes:
                    row = unique_record(data["summary"], method=f"{selection}_{size}", query=query)
                    ys.append(100 * row["accuracy"])
                    raw.append({"model": model, "query": query, "selection": selection, "knocked_out": size,
                                "n": row["n"], "correct": row["correct"], "accuracy_percent": 100*row["accuracy"],
                                "random_overlap_heads": data["controls"][str(size)]["overlap_heads"], "source": filename})
                ax.plot([0] + sizes, ys, color=color, marker=marker, ls=style, lw=1.2,
                        markersize=3.5, alpha=1 if selection == "selected" else 0.65)
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", loc="left", pad=7)
        ax.set_xticks([0] + sizes)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_xlabel("Knocked-out heads")
    axes[0].set_ylabel("Answer accuracy (%)")
    handles = [Line2D([0], [0], color=color, marker=marker, label=label) for _, label, color, marker in query_specs]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.53, 1.0), ncol=3,
               frameon=False, handlelength=1.8, columnspacing=2)
    fig.legend(handles=[Line2D([0], [0], color=INK, ls="-", label="Selected"),
                        Line2D([0], [0], color=INK, ls="--", label="Layer-matched random")],
               loc="upper center", bbox_to_anchor=(0.53, 0.90), ncol=2, frameon=False,
               handlelength=1.8, columnspacing=2)
    export_csv(name, raw)
    save_figure(fig, name)


def make_ablation(seeds: list[int]) -> None:
    name = "data_app_ablation"
    methods = [
        ("native", "Native", GRAY),
        ("native_text", "Evidence filtering", GRAY),
        ("head_tuning", "Head tuning", PURPLE),
        ("scoped_body", "Scoped adaptation", PURPLE),
        ("graphfirst", "Graph-first selection", CORAL),
        ("final_metadata", "Metadata-only reader", GRAY),
        ("final_attention", "Attention-only reader", TEAL),
        ("final", "CoReTrace", TEAL),
        ("fullft", "Full fine-tuning", CORAL),
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

    fig, axes = plt.subplots(1, 3, figsize=(6.75, 3.6), sharey=True)
    fig.subplots_adjust(left=0.22, right=0.985, bottom=0.16, top=0.90, wspace=0.20)
    y = np.arange(len(methods))
    for i, (model, ax) in enumerate(zip(MODELS, axes)):
        clean_axis(ax, "x")
        for j, (method, label, color) in enumerate(methods):
            row = unique_record(aggregates, model=model, method=method)
            mean, sd = row["mean_percent"], row["sample_sd_percent"]
            ax.errorbar(mean, j, xerr=sd, color=color, marker="o", markersize=5 if method == "final" else 4,
                        capsize=2, elinewidth=0.8, zorder=3)
            ax.text(mean + sd + 2, j, f"{mean:.1f}", ha="left", va="center", fontsize=8)
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[model]}", loc="left", pad=8)
        ax.set_xlim(0, 85)
        ax.set_xticks([0, 20, 40, 60, 80])
        ax.set_xlabel("Composed accuracy (%)")
        ax.set_yticks(y, [label for _, label, _ in methods])
        ax.set_ylim(len(methods) - 0.4, -0.6)
        ax.axhline(1.5, color=GRID, lw=0.7)
        ax.axhline(7.5, color=GRID, lw=0.7)
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

    fig, axes = plt.subplots(1, 3, figsize=(6.75, 3.06), sharey=True)
    fig.subplots_adjust(left=0.095, right=0.99, bottom=0.25, top=0.72, wspace=0.25)
    width = 0.22
    x = np.arange(3)
    low = min(row["delta_pp"] - row["sample_sd_percent"] for row in aggregates)
    low = 10 * np.floor((low - 7) / 10)
    for i, ((dataset, label, metric), ax) in enumerate(zip(datasets, axes)):
        clean_axis(ax)
        ax.axhline(0, color=INK, linewidth=0.8)
        for j, (method, method_label, color) in enumerate(methods):
            rows = [unique_record(aggregates, dataset=dataset, model=model, method=method) for model in MODELS]
            ys = [row["delta_pp"] for row in rows]
            sds = [row["sample_sd_percent"] for row in rows]
            pos = x + (j - 1) * width
            ax.bar(pos, ys, width=width, color=color, edgecolor="white", linewidth=0.4, label=method_label)
            ax.errorbar(pos, ys, yerr=sds, fmt="none", ecolor=INK, capsize=2, elinewidth=0.7)
            if method == "final":
                for xpos, value, sd in zip(pos, ys, sds):
                    ax.text(xpos, value - sd - 3.2, f"{value:+.1f}", ha="center", va="top", fontsize=8,
                            color=TEAL, fontweight="bold")
        ax.set_title(f"({chr(97+i)}) {label}\n{metric}", loc="left", pad=7)
        ax.set_xticks(x, ["Qwen3\n4B", "Qwen3\n8B", "Llama3.1\n8B"])
        ax.set_ylim(low, 15)
        ax.set_yticks(np.arange(10 * np.ceil(low / 20) * 2, 1, 20))
    axes[0].set_ylabel("Change from native (pp)")
    fig.legend(handles=[Patch(color=color, label=label) for _, label, color in methods],
               loc="upper center", bbox_to_anchor=(0.53, 1.0), ncol=3, frameon=False,
               columnspacing=1.6, handlelength=1.2)
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
