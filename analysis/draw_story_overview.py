#!/usr/bin/env python3
"""Draw the compact scientific overview as vector PDF and a preview PNG.

Run from the repository root with ``python analysis/draw_story_overview.py``.

The concrete example is the Walter II of Avesnes / James of Avesnes / Arsuf
case already documented in the paper's worked examples and original teaser.
The lower panel is explicitly schematic: it defines the exact contribution
of bridge tokens to one head before its output projection. It depicts no
measured attention weights, additional experimental observations, or serial
neural stages. All generated outputs remain under paper/figures.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "figures"
BLUE = "#1F77B4"
PURPLE = "#9467BD"
ORANGE = "#FF7F0E"
RED = "#C43333"
INK = "#17212B"
MUTED = "#50606E"


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "mathtext.fontset": "dejavusans",
            "font.size": 8,
            "text.color": INK,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    fig = plt.figure(figsize=(3.25, 3.02))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def text(x, y, s, size=8, color=INK, weight="normal", ha="center", **kw):
        return ax.text(
            x, y, s, fontsize=size, color=color, weight=weight,
            ha=ha, va="center", linespacing=1.15, **kw
        )

    def box(x, y, w, h, fill, edge, radius=0.017, lw=0.8):
        patch = FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0,rounding_size={radius}",
            linewidth=lw, edgecolor=edge, facecolor=fill,
        )
        ax.add_patch(patch)
        return patch

    def arrow(x1, x2, y, color=INK):
        ax.add_patch(
            FancyArrowPatch(
                (x1, y), (x2, y), arrowstyle="-|>",
                mutation_scale=8, linewidth=0.9, color=color,
                shrinkA=1.5, shrinkB=1.5,
            )
        )

    # The three questions receive the same original evidence paragraphs.
    text(0.035, 0.964, "Correct hops, failed composition", 9.2, weight="bold", ha="left")
    text(0.5, 0.909, "Same ten-paragraph context", 8.1, color=MUTED)

    box(0.035, 0.748, 0.282, 0.115, "#EDF5FA", BLUE)
    box(0.427, 0.748, 0.278, 0.115, "#F3EFF8", PURPLE)
    box(0.827, 0.748, 0.138, 0.115, "#FFF4E7", ORANGE)
    text(0.176, 0.8055, "Walter II\nof Avesnes", 8.1, weight="bold")
    text(0.566, 0.8055, "James\nof Avesnes", 8.1, weight="bold")
    text(0.896, 0.8055, "Arsuf", 8.0, weight="bold")
    arrow(0.320, 0.424, 0.800)
    arrow(0.708, 0.824, 0.800)
    text(0.372, 0.850, "father", 7.4)
    text(0.766, 0.850, "died in", 7.4)

    text(0.055, 0.685, r"$q_1$  Father: James", 8.3, ha="left")
    text(0.457, 0.685, "✓", 10, color=BLUE, weight="bold")
    text(0.540, 0.685, r"$q_2$  Died in: Arsuf", 8.3, ha="left")
    text(0.957, 0.685, "✓", 10, color=BLUE, weight="bold")

    text(0.5, 0.621, r"$q_{12}$  Where did Walter's father die?", 8.5)
    box(0.117, 0.509, 0.766, 0.079, "#FFF2F0", "#E4B8B3")
    text(0.5, 0.5485, "Native answer: Avesnes  ×", 9.1, color=RED, weight="bold")

    ax.plot((0.035, 0.965), (0.461, 0.461), color="#D4DCE2", linewidth=0.7)
    text(0.035, 0.422, "Diagnosing evidence use", 9.0, weight="bold", ha="left")
    text(0.965, 0.422, "schematic", 7.4, color=MUTED, ha="right")
    text(0.5, 0.363, "A bridge address can remain decodable\nwhen the composed answer fails.", 8.0)

    # Exact bridge-token contribution for a single attention row/head.
    # rho is normalized within B; m is the attention mass on B.
    text(0.5, 0.274, "Bridge contribution before output projection", 8.0)
    text(0.285, 0.197, r"$m$", 16.5, color=BLUE)
    text(0.430, 0.197, r"$\times$", 12.5)
    text(0.705, 0.197, r"$\sum_{k\in B}\rho_k v_k$", 13.0, color=PURPLE)
    text(0.109, 0.197, r"$c_B=$", 10.8)
    text(0.285, 0.083, "Paragraph\naccess mass", 8.0, color=BLUE)
    text(0.705, 0.083, "Within-paragraph\npattern and values", 8.0, color=PURPLE)

    # Retain a fixed final canvas; reject accidental clipping before export.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    for item in fig.findobj(matplotlib.text.Text):
        if not item.get_visible() or not item.get_text():
            continue
        bounds = item.get_window_extent(renderer)
        if bounds.x0 < canvas.x0 or bounds.y0 < canvas.y0 or bounds.x1 > canvas.x1 or bounds.y1 > canvas.y1:
            raise ValueError(f"Clipped text: {item.get_text()!r}; bounds={bounds.extents}")

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUT / "story_overview.pdf",
        metadata={
            "Title": "Correct hops, failed composition: diagnosing evidence use",
            "Subject": "Verified example and schematic attention factorization",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    fig.savefig(OUT / "story_overview.png", dpi=400)
    plt.close(fig)
    print("Wrote paper/figures/story_overview.pdf and .png (3.25 × 3.02 inches).")


if __name__ == "__main__":
    main()
