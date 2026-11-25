#!/usr/bin/env python3
"""Build manuscript figures from completed experiment summaries.

Run from the repository root: python analysis/plot_results.py
The existing summary readers, per-run aggregation and source manifests are the
only numerical pipeline. Main-text panels are drawn from the same collected
records as the appendix panels. No experiment values are specified in the
rendering functions, and no model/GPU or prediction archives are required.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import textwrap
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "paper" / "figures"
FIGURE_DATA = ROOT / "analysis" / "figure_data"
INPUT_PATHS: set[str] = set()
MODELS = ("qwen3_4b", "qwen3_8b", "llama3_8b")
MODEL_NAMES = {"qwen3_4b": "Qwen3-4B", "qwen3_8b": "Qwen3-8B", "llama3_8b": "Llama-3.1-8B"}
SHORT = {"qwen3_4b": "Qwen3\n4B", "qwen3_8b": "Qwen3\n8B", "llama3_8b": "Llama\n8B"}
BLUE, ORANGE, GREEN, PURPLE, RED = "#5E80B8", "#E09063", "#669780", "#9482AC", "#C46D69"
GRAY, LIGHT_GRAY, INK, GRID = "#92979E", "#C9CDD1", "#222222", "#DEDFE0"
MODEL_COLORS = [BLUE, GREEN, RED]
MODEL_MARKERS = ["o", "s", "^"]
COL = 3.25
WIDE = 6.75
plt.rcParams.update({"font.family":"sans-serif", "font.sans-serif":["DejaVu Sans", "Arial"],
    "mathtext.fontset":"dejavusans", "font.size":6.0, "axes.labelsize":6.2,
    "axes.titlesize":6.2, "axes.titleweight":"normal", "xtick.labelsize":5.3,
    "ytick.labelsize":5.3, "legend.fontsize":5.5, "axes.edgecolor":INK,
    "axes.labelcolor":INK, "text.color":INK, "xtick.color":INK,"ytick.color":INK,
    "axes.linewidth":0.55,"lines.linewidth":1.05,"lines.markersize":3.3,
    "figure.facecolor":"white","axes.facecolor":"white","savefig.facecolor":"white",
    "pdf.fonttype":42,"ps.fonttype":42,"svg.fonttype":"none","axes.unicode_minus":True})

# The following data access, selection, aggregation and source tracing interfaces
# retain the original analysis/plot_results.py conventions.
def read_json(relative_path: str | Path) -> Any:
    path = ROOT / relative_path
    INPUT_PATHS.add(path.relative_to(ROOT).as_posix())
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)

def source(model: str, relative_path: str) -> str:
    return f"outputs/{model}/{relative_path}"

def unique_record(rows: list[dict[str, Any]], **criteria: Any) -> dict[str, Any]:
    matches = [row for row in rows if all(row.get(k) == v for k,v in criteria.items())]
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
        writer.writeheader(); writer.writerows(rows)

def save_figure(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
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
            or bounds.y0 < canvas.y0 - 0.5 or bounds.y1 > canvas.y1 + 0.5):
            raise ValueError(f"Figure text extends beyond canvas: {name}: {item.get_text()}")
    fig.savefig(FIGURES / f"{name}.pdf", metadata={"Creator":"CoReTrace analysis/plot_results.py"})
    fig.savefig(FIGURES / f"{name}.png", dpi=300)
    plt.close(fig)
    print(f"Wrote paper/figures/{name}.pdf and .png")

def clean_axis(ax: plt.Axes, grid_axis: str = "y", *, box: bool = False) -> None:
    ax.spines[["top","right"]].set_visible(box)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.4, linestyle="--", alpha=.9)
    ax.set_axisbelow(True); ax.tick_params(length=2.4,width=.55,pad=2.0)

def inset_legend(ax, loc="best", **kw):
    defaults=dict(loc=loc, frameon=True, fancybox=False, framealpha=.94,
                  facecolor="white", edgecolor="#C8C8C8", fontsize=5.1,
                  borderpad=.25, labelspacing=.28, handlelength=1.4,
                  handletextpad=.35, columnspacing=.65, borderaxespad=.35)
    defaults.update(kw)
    legend=ax.legend(**defaults)
    legend.get_frame().set_linewidth(.4)
    return legend

def bars(ax, x, values, width, color, *, errors=None, label=None, labels=False, decimals=0, label_offset=1.6):
    container = ax.bar(x, values, width, color=color, edgecolor=INK, linewidth=.4, label=label,zorder=3)
    if errors is not None:
        ax.errorbar(x,values,yerr=errors,fmt="none",ecolor=INK,elinewidth=.7,capsize=2,capthick=.7,zorder=4)
    if labels:
        for xpos,value in zip(x,values):
            ax.text(xpos,value+label_offset,f"{value:.{decimals}f}",ha="center",va="bottom",fontsize=5.3)
    return container

def mean_sd(values):
    return statistics.mean(values), statistics.stdev(values) if len(values)>1 else 0.0

def seed_values(model: str,dataset: str,method: str,seeds: list[int],query: str | None=None):
    pipeline="evaluation_fullft" if method=="fullft" else "evaluation"
    query=query or ("composed" if dataset=="core" else dataset)
    values=[]
    for seed in ([seeds[0]] if method=="native" else seeds):
        filename=source(model,f"seed{seed}/{pipeline}/{dataset}/summary.json")
        stored_method="FullFT" if method=="fullft" else method
        row=unique_record(read_json(filename)["summary"],method=stored_method,query=query)
        numerator=row["logprob_correct"] if dataset=="mmlu" else row["correct"]
        values.append({"model":model,"seed":seed,"method":method,"dataset":dataset,"query":query,
            "n":row["n"],"correct":numerator,"accuracy_percent":100*numerator/row["n"],
            "metric":"option_probability_accuracy" if dataset=="mmlu" else "accuracy","source":filename})
    return values

# Compact rendering layer. Each helper accepts records from the collectors below.
def render_composition(composition):
    """Expose composition success and failure within the fixed native population."""
    fig,ax=plt.subplots(figsize=(COL,1.45))
    fig.subplots_adjust(left=.285,right=.955,bottom=.25,top=.78)
    y=np.arange(len(MODELS))[::-1]
    rows=[unique_record(composition,model=m) for m in MODELS]
    success=np.array([100*r["composition_successes"]/r["both_constituents_correct"] for r in rows])
    failure=np.array([r["conditional_failure_percent"] for r in rows])
    if not np.allclose(success+failure,100):
        raise ValueError("Composition outcomes do not partition the native constituent-correct population")
    ax.barh(y,success,height=.60,color=BLUE,edgecolor="white",linewidth=.6,label="Composed correct",zorder=3)
    ax.barh(y,failure,left=success,height=.60,color=ORANGE,edgecolor="white",linewidth=.6,label="Composed incorrect",zorder=3)
    for yi,row,ok,bad in zip(y,rows,success,failure):
        ax.text(ok/2,yi,f"{row['composition_successes']} ({ok:.1f}%)",
                ha="center",va="center",fontsize=6.0,color="white",fontweight="bold")
        ax.text(ok+bad/2,yi,f"{row['composition_failures']} ({bad:.1f}%)",
                ha="center",va="center",fontsize=6.0,color=INK,fontweight="bold")
    ax.set(yticks=y,yticklabels=[f"{MODEL_NAMES[m]}\n$n={r['both_constituents_correct']}$"
                              for m,r in zip(MODELS,rows)],
           xlim=(0,100),ylim=(-.55,len(MODELS)-.45),xticks=[0,50,100],
           xlabel="Share of constituent-correct sources (%)")
    ax.tick_params(axis="y",length=0,pad=4,labelsize=6.0)
    ax.tick_params(axis="x",length=2.4,pad=2,labelsize=6.0)
    ax.xaxis.label.set_size(6.0)
    ax.spines[["top","right","left"]].set_visible(False)
    handles,labels=ax.get_legend_handles_labels()
    fig.legend(handles,labels,loc="upper center",bbox_to_anchor=(.54,.995),
               ncol=2,frameon=False,fontsize=6.0,handlelength=1.25,
               handletextpad=.35,columnspacing=.9)
    save_figure(fig,"data_main_composition")


def render_diagnosis(readouts):
    fig,ax=plt.subplots(figsize=(COL,1.65)); fig.subplots_adjust(left=.14,right=.985,bottom=.23,top=.97)
    clean_axis(ax); x=np.arange(len(MODELS)); width=.23
    specs=[("metadata","Metadata",LIGHT_GRAY),("attention","Attention",BLUE),("full","Full",ORANGE)]
    for j,(key,label,color) in enumerate(specs):
        vals=[unique_record(readouts,model=m,feature_set=key)["accuracy_percent"] for m in MODELS]
        bars(ax,x+(j-1)*width,vals,width,color,label=label,labels=key=="full",decimals=1,label_offset=2)
    ax.set(xticks=x,xticklabels=[SHORT[m] for m in MODELS],ylim=(0,116),yticks=[0,25,50,75,100],ylabel="Bridge-address accuracy (%)")
    inset_legend(ax,"upper center",ncol=3)
    save_figure(fig,"data_fig3_diagnosis")

def render_causal(factors,contrasts,access):
    """Show the crossed conditions and their measured interaction together.

    Cell values and paired contrasts use the same 100 receivers. Intervals are
    the recorded quadruplet-bootstrap intervals for contrasts, not invented
    cell-level uncertainty. Address specificity uses a separate test population
    and is rendered separately below.
    """
    fig=plt.figure(figsize=(WIDE,2.45))
    condition_rows=(("native","conditional_only"),("mass_only","both"))
    contrast_keys=("conditional_effect_native_mass","conditional_effect_fixed_mass")
    for i,model in enumerate(MODELS):
        color=MODEL_COLORS[i]
        left=.025+i*.327
        values=np.array([[unique_record(factors,model=model,method=key)["accuracy_percent"]
                          for key in row] for row in condition_rows])
        effects=[unique_record(contrasts,model=model,contrast=key) for key in contrast_keys]
        estimate=np.array([row["estimate_pp"] for row in effects])
        low=np.array([row["CI95_low_pp"] for row in effects])
        high=np.array([row["CI95_high_pp"] for row in effects])
        interaction=unique_record(contrasts,model=model,contrast="interaction")
        if not np.allclose(values[:,1]-values[:,0],estimate):
            raise ValueError(f"Crossed cells and pattern contrasts disagree for {model}")
        if not np.isclose(estimate[1]-estimate[0],interaction["estimate_pp"]):
            raise ValueError(f"Pattern contrasts and interaction disagree for {model}")

        fig.text(left+.155,.967,f"({chr(97+i)}) {MODEL_NAMES[model]}",
                 ha="center",va="top",fontsize=7.2,fontweight="bold",color=INK)

        # Equal-area cells expose the actual 2-by-2 design. Color identifies
        # the combined condition; it does not encode a simulated attention map.
        matrix=fig.add_axes([left,.555,.31,.325])
        matrix.set(xlim=(0,1),ylim=(0,1));matrix.axis("off")
        matrix.text(.66,.98,"Composed accuracy (%)",ha="center",va="top",fontsize=6.1)
        matrix.text(.01,.72,"Access mass",ha="left",va="center",fontsize=5.9)
        for j,label in enumerate(("Receiver","Direct-query")):
            matrix.text(.55+j*.30,.72,label,ha="center",va="center",fontsize=6.0)
        for row,label in enumerate(("Native","Calibrated")):
            y=.365-row*.335
            matrix.text(.01,y+.14,label,ha="left",va="center",fontsize=6.1)
            for col in range(2):
                x=.405+col*.30
                combined=row==1 and col==1
                face=matplotlib.colors.to_rgba(color,.16) if combined else "#F2F3F5"
                matrix.add_patch(Rectangle((x,y),.29,.28,facecolor=face,
                                           edgecolor=color if combined else "#CFD3D7",
                                           linewidth=.65 if combined else .45))
                matrix.text(x+.145,y+.14,f"{values[row,col]:.0f}",ha="center",va="center",
                            fontsize=8.4,fontweight="bold" if combined else "normal",color=INK)

        ax=fig.add_axes([left+.065,.19,.225,.285])
        clean_axis(ax)
        ax.axhline(0,color=GRAY,linestyle=":",lw=.8,zorder=2)
        ax.errorbar([0,1],estimate,yerr=[estimate-low,high-estimate],
                    fmt=MODEL_MARKERS[i]+"-",color=color,markeredgecolor="white",
                    markeredgewidth=.45,markersize=4.0,capsize=2.4,capthick=.8,
                    elinewidth=.9,linewidth=1.25,zorder=4)
        for x,value in enumerate(estimate):
            ax.text(x+.12,value+(2.2 if x==0 else 0),f"{value:+.0f}",ha="left",
                    va="bottom" if x==0 else "center",fontsize=6.5,
                    fontweight="bold",color=INK,zorder=5,
                    bbox={"facecolor":"white","edgecolor":"none","pad":.35})
        ax.set(title="Direct-query pattern effect",xlim=(-.24,1.42),
               xticks=[0,1],xticklabels=["Native","Calibrated"],
               ylim=(-12,24),yticks=[-10,0,10,20],xlabel="Access mass")
        ax.set_title("Direct-query pattern effect",fontsize=6.3,pad=3)
        ax.tick_params(labelsize=5.8)
        ax.xaxis.label.set_size(5.8)
        if i==0:
            ax.set_ylabel("Effect on accuracy (pp)",fontsize=6.0,labelpad=3)
        interval=f"[{interaction['CI95_low_pp']:.0f}, {interaction['CI95_high_pp']:.0f}]"
        fig.text(left+.155,.035,
                 f"Interaction: {interaction['estimate_pp']:+.0f} pp  {interval}",
                 ha="center",va="center",fontsize=6.6,fontweight="bold",color=INK)
    save_figure(fig,"data_main_causal_pair")
    render_access_controls(access)


def render_access_controls(access):
    """Preserve the separate 1,000-source address intervention in the appendix."""
    fig,ax=plt.subplots(figsize=(COL,1.85))
    fig.subplots_adjust(left=.16,right=.985,bottom=.24,top=.97)
    clean_axis(ax);x=np.arange(len(MODELS));width=.23
    specs=[("oracle_second_paragraph","Bridge",BLUE),("oracle_first_paragraph","Root",GRAY),("lengthmatched_other_paragraph","Other",ORANGE)]
    bounds=[]
    for i,(key,label,color) in enumerate(specs):
        r=[unique_record(access,model=m,method=key) for m in MODELS]
        vals=np.array([p["delta_pp"] for p in r]);lo=np.array([p["CI95_low_pp"] for p in r]);hi=np.array([p["CI95_high_pp"] for p in r]);bounds.extend(lo);bounds.extend(hi)
        pos=x+(i-1)*width;bars(ax,pos,vals,width,color,label=label)
        ax.errorbar(pos,vals,yerr=[vals-lo,hi-vals],fmt="none",ecolor=INK,elinewidth=.75,capsize=2,zorder=4)
    ax.axhline(0,color=INK,lw=.65)
    ax.set(xticks=x,xticklabels=[SHORT[m] for m in MODELS],
           ylim=(np.floor(min(bounds)/5)*5-1,np.ceil(max(bounds)/5)*5+9),
           ylabel="EM change (pp)",yticks=[-20,-10,0,10,20])
    inset_legend(ax,"upper center",fontsize=5.5,ncol=3)
    save_figure(fig,"data_app_access_controls")


def heatmap_bins(matrices,step=.02):
    # Explicit fixed-width score bins, preserving every measured head's bin.
    # The full-precision scores are exported separately and remain unchanged.
    nb=int(np.ceil(max(float(np.abs(a).max()) for a in matrices)/step))
    bins=[np.clip(np.floor(a/step).astype(int)+nb,0,2*nb-1) for a in matrices]
    return nb,bins

def head_sets(ranked,active):
    k=len(active)
    def top(field):
        ordered=sorted(ranked,key=lambda r:(-r[field],r["layer"],r["head"]))
        return {(r["layer"],r["head"]) for r in ordered[:k]}
    return [set(active),top("direct_target_all_question_mean"),top("composed_all_question_mean")]


def intersection_rows(sets):
    counts={}
    for head in set.union(*sets):
        membership=tuple(int(head in group) for group in sets)
        counts[membership]=counts.get(membership,0)+1
    # Exact, mutually exclusive intersection sizes; include every nonempty intersection.
    return sorted(counts.items(),key=lambda row:(sum(row[0]),row[0]),reverse=True)


def draw_upset(fig, slot, sets, title):
    gs=slot.subgridspec(2,1,height_ratios=[1.9,1],hspace=.06)
    top=fig.add_subplot(gs[0]);bot=fig.add_subplot(gs[1],sharex=top)
    rows=intersection_rows(sets);x=np.arange(len(rows));n=[r[1] for r in rows]
    top.bar(x,n,width=.65,color="#222222",zorder=3)
    top.set_title(title,pad=3);top.set_ylabel("Heads",labelpad=1.2)
    top.set_ylim(0,max(n)*1.22);top.set_xlim(-.55,len(rows)-.45)
    top.tick_params(axis="x",bottom=False,labelbottom=False)
    top.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4,integer=True))
    clean_axis(top,"y");top.spines["bottom"].set_visible(False)
    for i,v in enumerate(n):top.text(i,v+.025*max(n),str(v),ha="center",va="bottom",fontsize=5.1)
    for j in range(3):
        if j%2==0:bot.axhspan(j-.5,j+.5,color="#F0F0F0",zorder=0)
    for i,(pattern,_) in enumerate(rows):
        ys=[j for j,v in enumerate(pattern) if v]
        bot.scatter([i]*3,range(3),s=9,color="#C5C5C5",zorder=1,edgecolors="none")
        if len(ys)>1:bot.plot([i,i],[min(ys),max(ys)],color="#222222",lw=.8,zorder=2)
        bot.scatter([i]*len(ys),ys,s=12,color="#222222",zorder=3,edgecolors="none")
    bot.set(yticks=[0,1,2],yticklabels=["Ranked","Direct","Composed"],ylim=(2.5,-.5),xticks=[])
    bot.tick_params(axis="y",length=0,pad=1.5,labelsize=4.9)
    for spine in bot.spines.values():spine.set_visible(False)


def render_localization_main(bins,selected,nb,step=.02):
    # Two representative architecture families; all three full maps and exact
    # head-set intersections remain in the appendix. Use a common score scale.
    fig=plt.figure(figsize=(COL,1.67))
    gs=fig.add_gridspec(1,3,left=.12,right=.88,bottom=.20,top=.86,
                        wspace=.37,width_ratios=[1,1,.062])
    edges=np.arange(-nb,nb+1)*step
    cmap=plt.get_cmap("RdBu_r",2*nb);norm=BoundaryNorm(edges,cmap.N)
    for i,j in enumerate((0,2)):
        grid=bins[j];ax=fig.add_subplot(gs[i])
        im=ax.imshow((grid-nb+.5)*step,cmap=cmap,norm=norm,
                     interpolation="nearest",aspect="equal")
        for layer,head in selected[j]:
            ax.add_patch(Rectangle((head-.5,layer-.5),1,1,fill=False,ec="#383838",lw=.24))
        ax.set(title=f"({chr(97+i)}) {MODEL_NAMES[MODELS[j]]}",xlabel="Head",
               xticks=[0,8,16,24],yticks=np.arange(0,grid.shape[0],8))
        if i==0:ax.set_ylabel("Layer",labelpad=2)
        ax.tick_params(length=1.7,pad=1.5,labelsize=5.1)
        ax.set_title(f"({chr(97+i)}) {MODEL_NAMES[MODELS[j]]}",fontsize=5.8,pad=4)
    cb=fig.colorbar(im,cax=fig.add_subplot(gs[2]),orientation="vertical",ticks=[-.3,0,.3])
    cb.ax.minorticks_off();cb.ax.tick_params(length=1.5,pad=1.5,labelsize=5.0)
    cb.set_label("Attention gap",fontsize=5.5,labelpad=2);cb.outline.set_visible(False)
    save_figure(fig,"data_main_localization")


def render_localization_overlap_all(sets_by_model):
    fig=plt.figure(figsize=(WIDE,2.05));gs=fig.add_gridspec(1,3,left=.12,right=.985,top=.88,bottom=.12,wspace=.82)
    for i,m in enumerate(MODELS):draw_upset(fig,gs[i],sets_by_model[m],MODEL_NAMES[m]+f" (K={len(sets_by_model[m][0])})")
    save_figure(fig,"data_app_head_overlap")


def draw_profile(ax,profiles):
    clean_axis(ax,"both",box=True)
    for i,(m,c,marker) in enumerate(zip(MODELS,MODEL_COLORS,MODEL_MARKERS)):
        rows=sorted((r for r in profiles if r["model"]==m),key=lambda r:r["layer"])
        ax.plot([r["layer"] for r in rows],[r["mean_score"] for r in rows],color=c,marker=marker,markersize=1.8,markeredgewidth=.25,markeredgecolor="white",label=["4B","8B","L8B"][i])
    ax.axhline(0,lw=.5,color=GRAY);ax.set(title="(a) Layer profile",xlabel="Layer",ylabel="Mean gap",xlim=(0,max(r["layer"] for r in profiles)),ylim=(-.005,.128),xticks=[0,10,20,30],yticks=[0,.04,.08,.12])
    inset_legend(ax,"upper right",fontsize=4.8,ncol=1,labelspacing=.17)


def draw_necessity(ax,raw,measured_sizes):
    clean_axis(ax,"both",box=True);m=MODELS[-1];q="composed"
    base=unique_record(raw,model=m,query=q,selection="native")["accuracy_percent"]
    sizes=measured_sizes[m];x=[0]+sizes
    for sel,label,c,mark in [("selected","Ranked",ORANGE,"o"),("random","Random",GRAY,"s")]:
        vals=[base]+[unique_record(raw,model=m,query=q,selection=sel,knocked_out=k)["accuracy_percent"] for k in sizes]
        ax.plot(x,vals,color=c,marker=mark,markeredgecolor="white",markeredgewidth=.35,label=label,zorder=3)
    ax.set(title="(b) Head knockout",xticks=[0,20,40,80],xlim=(-4,max(x)+5),ylim=(0,base+7),xlabel="Heads removed",ylabel="Composed EM (%)",yticks=[0,10,20,30,40])
    inset_legend(ax,"upper right",fontsize=4.8,labelspacing=.20)


def render_head_pair(profiles,raw,measured_sizes):
    fig,axes=plt.subplots(1,2,figsize=(COL,1.73));fig.subplots_adjust(left=.13,right=.98,bottom=.22,top=.88,wspace=.46)
    draw_profile(axes[0],profiles);draw_necessity(axes[1],raw,measured_sizes)
    save_figure(fig,"data_main_head_pair")


def render_necessity(raw,measured_sizes):
    # Identical y scales within each query row permit direct model comparison.
    # All measured doses and controls are retained; no interpolation of new data.
    fig,axes=plt.subplots(3,3,figsize=(WIDE,3.10),sharex=True,sharey="row")
    fig.subplots_adjust(left=.105,right=.98,bottom=.12,top=.92,wspace=.19,hspace=.25)
    queries=[("composed","Composed"),("direct_first","First hop"),("direct_target","Second hop")]
    for i,(q,label) in enumerate(queries):
        all_delta=[]
        for j,m in enumerate(MODELS):
            ax=axes[i,j];clean_axis(ax,"both",box=True)
            sizes=measured_sizes[m];base=unique_record(raw,model=m,query=q,selection="native")["accuracy_percent"]
            for sel,legend,c,mark in [("selected","Ranked",ORANGE,"o"),("random","Random",BLUE,"s")]:
                vals=[0]+[unique_record(raw,model=m,query=q,selection=sel,knocked_out=k)["accuracy_percent"]-base for k in sizes]
                all_delta.extend(vals)
                ax.plot([0]+sizes,vals,marker=mark,color=c,label=legend,markersize=2.7,
                        markeredgecolor="white",markeredgewidth=.28,zorder=3)
            ax.axhline(0,color=GRAY,lw=.55,linestyle=":")
            ax.set_xticks([0]+sizes);ax.set_xlim(-4,max(sizes)+4)
            if i==0:ax.set_title(MODEL_NAMES[m],pad=4)
            if j==0:ax.set_ylabel(label+"\nEM change (pp)",labelpad=3)
            if i==2:ax.set_xlabel("Heads removed",labelpad=2)
        lower=10*np.floor(min(all_delta)/10);upper=max(7,10*np.ceil(max(all_delta)/10))
        axes[i,0].set_ylim(lower-2,upper+1)
        axes[i,0].yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4,integer=True))
    inset_legend(axes[0,0],"lower left",fontsize=5.0,ncol=1,labelspacing=.20)
    save_figure(fig,"data_app_necessity")


def render_content(aggregated):
    fig,axes=plt.subplots(1,2,figsize=(COL,1.67),sharey=True);fig.subplots_adjust(left=.13,right=.99,bottom=.19,top=.87,wspace=.26)
    specs=[("edited_new_follow","(a) Edited value"),("original_correct_then_new","(b) Joint EM")];x=np.arange(3);width=.32
    for ax,(key,title) in zip(axes,specs):
        clean_axis(ax,"y",box=True)
        for j,(method,label,c) in enumerate([("native","Native",BLUE),("final","CoReTrace",ORANGE)]):
            r=[unique_record(aggregated,model=m,method=method,metric=key) for m in MODELS]
            bars(ax,x+(j-.5)*width,[v["mean_percent"] for v in r],width,c,errors=[v["sample_sd_percent"] for v in r],label=label)
        ax.set(title=title,xticks=x,xticklabels=["4B","8B","L8B"],ylim=(0,125),yticks=[0,25,50,75,100])
    axes[0].set_ylabel("Queries (%)");inset_legend(axes[0],"upper left",fontsize=4.8,labelspacing=.15)
    save_figure(fig,"data_fig5_content")


def render_ambiguity(rows):
    # Two matched policies, same checkpoint and same 103-source population.
    fig,axes=plt.subplots(1,2,figsize=(COL,1.67),sharey=True);fig.subplots_adjust(left=.13,right=.99,bottom=.19,top=.87,wspace=.26)
    x=np.arange(3); width=.32
    for ax,(key,title) in zip(axes,[("bridge_selection_accuracy","(a) Bridge address"),("answer_accuracy_mean","(b) Composed EM")]):
        clean_axis(ax,"y",box=True)
        for i,(method,label,c) in enumerate([("graphfirst","Input order",BLUE),("final","Full reader",ORANGE)]):
            data=[unique_record(rows,model=m,method=method) for m in MODELS]
            errors=[100*r["answer_accuracy_sample_std"] for r in data] if key=="answer_accuracy_mean" else None
            bars(ax,x+(i-.5)*width,[100*r[key] for r in data],width,c,errors=errors,label=label)
        ax.set(title=title,xticks=x,xticklabels=["4B","8B","L8B"],ylim=(0,125),yticks=[0,25,50,75,100])
    axes[0].set_ylabel("Accuracy (%)");inset_legend(axes[0],"upper left",fontsize=4.8,labelspacing=.15)
    save_figure(fig,"data_main_ambiguity")


def render_ablation(aggregates):
    metrics=[("direct_first","First hop"),("all3","All three"),("gsm8k","GSM8K")]
    fig,ax=plt.subplots(figsize=(COL,1.67));fig.subplots_adjust(left=.14,right=.98,bottom=.19,top=.97)
    clean_axis(ax,"y",box=True);x=np.arange(3);width=.33;m=MODELS[-1]
    for j,(restored,label,color) in enumerate([(False,"Adaptation",BLUE),(True,"+ Restoration",ORANGE)]):
        data=[unique_record(aggregates,model=m,query=q,projection_restoration=restored) for q,_ in metrics]
        bars(ax,x+(j-.5)*width,[r["mean_percent"] for r in data],width,color,errors=[r["sample_sd_percent"] for r in data],label=label,labels=True,decimals=1,label_offset=2)
    ax.set(xticks=x,xticklabels=[v for _,v in metrics],ylim=(0,119),yticks=[0,25,50,75,100],ylabel="Accuracy (%)")
    inset_legend(ax,"upper center",ncol=2)
    save_figure(fig,"data_main_restoration")
    fig,axes=plt.subplots(1,3,figsize=(WIDE,1.55),sharey=True);fig.subplots_adjust(left=.08,right=.985,bottom=.19,top=.84,wspace=.20)
    for ax,(key,title) in zip(axes,metrics):
        clean_axis(ax,"y",box=True)
        for j,(restored,label,c) in enumerate([(False,"Adaptation",BLUE),(True,"+ Restoration",ORANGE)]):
            data=[unique_record(aggregates,model=m,query=key,projection_restoration=restored) for m in MODELS]
            bars(ax,x+(j-.5)*width,[r["mean_percent"] for r in data],width,c,errors=[r["sample_sd_percent"] for r in data],label=label)
        ax.set(title=title,xticks=x,xticklabels=["Qwen3-4B","Qwen3-8B","Llama-8B"],ylim=(0,125),yticks=[0,25,50,75,100])
    axes[0].set_ylabel("Accuracy (%)");inset_legend(axes[0],"upper center",ncol=2,fontsize=4.8,labelspacing=.15)
    save_figure(fig,"data_app_ablation")


def render_capabilities(aggregates):
    fig,axes=plt.subplots(1,3,figsize=(WIDE,1.63),sharey=True);fig.subplots_adjust(left=.08,right=.985,bottom=.19,top=.84,wspace=.20)
    x=np.arange(3);width=.23
    for ax,(dataset,title) in zip(axes,[("hotpot","HotpotQA"),("mmlu","MMLU"),("gsm8k","GSM8K")]):
        clean_axis(ax,"y",box=True)
        for j,(method,label,c) in enumerate([("native","Native",BLUE),("fullft","Full fine-tuning",LIGHT_GRAY),("final","CoReTrace",ORANGE)]):
            data=[unique_record(aggregates,model=m,dataset=dataset,method=method) for m in MODELS]
            bars(ax,x+(j-1)*width,[r["mean_percent"] for r in data],width,c,errors=[r["sample_sd_percent"] for r in data],label=label)
        ax.set(title=title,xticks=x,xticklabels=["Qwen3-4B","Qwen3-8B","Llama-8B"],ylim=(0,125),yticks=[0,25,50,75,100])
    axes[0].set_ylabel("Accuracy (%)");inset_legend(axes[0],"upper center",ncol=3,fontsize=4.6,labelspacing=.13,handlelength=1.0,columnspacing=.4)
    save_figure(fig,"data_app_capabilities")

# Original per-source collectors. New main panels reuse their records directly.
def collect_composition(seeds: list[int]):
    composition=[]
    for model in MODELS:
        filename=source(model,f"seed{seeds[0]}/evaluation/core/summary.json")
        row=unique_record(read_json(filename)["conditional_composition"],method="native")
        denominator=row["both_constituents_correct"]
        composition.append({"model":model,"total_test_sources":row["n_sources"],"both_constituents_correct":denominator,"composition_failures":row["composition_failures"],"composition_successes":denominator-row["composition_failures"],"conditional_failure_percent":100*row["composition_failures"]/denominator,"source":filename})
    return composition


def make_composition(seeds: list[int]) -> None:
    composition=collect_composition(seeds)
    export_csv("data_main_composition",composition)
    render_composition(composition)


def make_diagnosis(seeds: list[int]) -> None:
    name="data_fig3_diagnosis"
    composition=collect_composition(seeds)
    readouts,overall_readouts=[],[]
    subpopulation_file="analysis/internal/readout_validation.json"
    subpopulation_data=read_json(subpopulation_file)
    for model in MODELS:
        filename=unique_record(composition,model=model)["source"]
        overall_file=source(model,"native_readout/complete.json");diagnostic=read_json(overall_file)["diagnostics"]
        population=unique_record(subpopulation_data,directory=source(model,"native_readout"));subgroup=population["native_composition_failure_readout"]
        for features in ("full","attention","metadata"):
            row=subgroup[features]
            if row["n"]!=unique_record(composition,model=model)["composition_failures"]:raise ValueError(f"Composition-failure subpopulation mismatch: {model}/{features}")
            readouts.append({"model":model,"feature_set":features,"n":row["n"],"correct":row["correct"],"accuracy_percent":100*row["correct"]/row["n"],"subpopulation":"native_both_constituents_correct_composed_incorrect","source":subpopulation_file,"reader_directory":source(model,"native_readout"),"composition_source":filename})
            row=diagnostic[features]["test"]
            overall_readouts.append({"model":model,"feature_set":features,"n":row["n"],"correct":row["correct"],"accuracy_percent":100*row["correct"]/row["n"],"subpopulation":"all_test_sources","source":overall_file})
    export_csv(f"{name}_composition",composition);export_csv(f"{name}_address_readout",readouts);export_csv(f"{name}_address_readout_overall",overall_readouts)
    render_diagnosis(readouts)


def make_causal() -> None:
    name="data_fig4_causal";factors,contrasts,access=[],[],[]
    for model in MODELS:
        filename=source(model,"causal_factorization/summary.json");data=read_json(filename)
        for row in data["summary"]:
            factors.append({"model":model,"method":row["method"],"n":row["n"],"correct":row["correct"],"accuracy_percent":100*row["accuracy"],"clusters":data["factorial_accuracy"]["clusters"],"source":filename})
        for contrast,row in data["factorial_accuracy"]["contrasts"].items():
            contrasts.append({"model":model,"contrast":contrast,"estimate_pp":100*row["estimate"],"CI95_low_pp":100*row["paired_cluster_CI95"][0],"CI95_high_pp":100*row["paired_cluster_CI95"][1],"n":data["factorial_accuracy"]["n"],"clusters":data["factorial_accuracy"]["clusters"],"source":filename})
        filename=source(model,"causal_access/summary.json");data=read_json(filename)
        for method in ("oracle_second_paragraph","oracle_first_paragraph","lengthmatched_other_paragraph"):
            row=unique_record(data["paired_comparisons"],method_before="native",method_after=method,query="composed",metric="correct")
            access.append({"model":model,"method":method,"n":row["n"],"native_correct":row["before"],"intervened_correct":row["after"],"delta_pp":100*row["delta"],"CI95_low_pp":100*row["paired_cluster_CI95"][0],"CI95_high_pp":100*row["paired_cluster_CI95"][1],"clusters":row["cluster_count"],"source":filename})
    export_csv(f"{name}_factorial",factors);export_csv(f"{name}_factorial_contrasts",contrasts);export_csv(f"{name}_access_controls",access)
    render_causal(factors,contrasts,access)


def make_content(seeds: list[int]) -> None:
    name="data_fig5_content";raw,aggregated=[],[]
    methods=("native","native_budget","body","final");fields=("original_old_correct","edited_new_follow","edited_old_persistence","original_correct_then_new")
    for model in MODELS:
        for seed in seeds:
            filename=source(model,f"seed{seed}/causal_content/summary.json");data=read_json(filename)
            for method in methods:
                row=unique_record(data["summary"],variant=method,pool="all_sources");actual=unique_record(data["summary"],variant=method,pool="actual_swaps")
                for field in fields:
                    raw.append({"model":model,"seed":seed,"method":method,"metric":field,"n":row["n"],"actual_swaps":actual["n"],"count":row[field],"rate_percent":100*row[field]/row["n"],"source":filename})
        for method in methods:
            for field in fields:
                rows=[row for row in raw if row["model"]==model and row["method"]==method and row["metric"]==field]
                mean,sd=mean_sd([row["rate_percent"] for row in rows])
                if method in {"native","native_budget"} and sd>1e-10:raise ValueError(f"Native content references disagree across seed files: {model}/{method}")
                aggregated.append({"model":model,"method":method,"metric":field,"n_per_run":rows[0]["n"],"actual_swaps":rows[0]["actual_swaps"],"recorded_runs":1 if method in {"native","native_budget"} else len(rows),"mean_percent":mean,"sample_sd_percent":sd,"sources":";".join(row["source"] for row in rows)})
    export_csv(f"{name}_seed_values",raw);export_csv(f"{name}_aggregated",aggregated)
    metric_labels={"edited_new_follow":"Edited-value following","original_correct_then_new":"Joint correctness"}
    export_csv(f"{name}_plotted",[{**r,"display_label":metric_labels[r["metric"]]} for r in aggregated if r["method"] in {"native","final"} and r["metric"] in metric_labels])
    render_content(aggregated)


def make_localization():
    name="data_app_localization";rows,matrices,selected=[],[],[]
    sets_by_model={};membership=[];overlaps=[]
    for model in MODELS:
        filename=source(model,"discovery/ranking.json");ranked=read_json(filename)["ranking"]
        selection_file=source(model,"discovery/SELECTION_FROZEN.json");selection=read_json(selection_file)
        active={(int(layer),head) for layer,heads in selection["head_map"].items() for head in heads}
        n_layers=max(r["layer"] for r in ranked)+1;n_heads=max(r["head"] for r in ranked)+1
        matrix=np.full((n_layers,n_heads),np.nan)
        for rank,row in enumerate(ranked,1):
            matrix[row["layer"],row["head"]]=row["score"]
            rows.append({"model":model,"rank":rank,**row,"selected":(row["layer"],row["head"]) in active,"source":filename,"selection_source":selection_file})
        if np.isnan(matrix).any():raise ValueError(f"Incomplete all-head ranking: {model}")
        matrices.append(matrix);selected.append(active)
        sets=head_sets(ranked,active);sets_by_model[model]=sets
        for l,h in sorted(set.union(*sets)):
            membership.append(dict(model=model,layer=l,head=h,k=len(active),ranked=int((l,h) in sets[0]),direct=int((l,h) in sets[1]),composed=int((l,h) in sets[2]),source=filename,selection_source=selection_file))
        for pattern,count in intersection_rows(sets):
            overlaps.append(dict(model=model,k=len(active),ranked=pattern[0],direct=pattern[1],composed=pattern[2],intersection_count=count,source=filename,selection_source=selection_file))
    export_csv("data_app_head_membership",membership)
    export_csv("data_app_head_intersections",overlaps)
    export_csv(name,rows)
    profiles=[]
    for model,matrix in zip(MODELS,matrices):
        for layer,(mean,peak) in enumerate(zip(matrix.mean(axis=1),matrix.max(axis=1))):
            profiles.append({"model":model,"layer":layer,"mean_score":float(mean),"maximum_score":float(peak),"heads_per_layer":matrix.shape[1],"source":source(model,"discovery/ranking.json")})
    export_csv(f"{name}_layer_profiles",profiles)
    nb,bins=heatmap_bins(matrices);export_csv("data_main_localization_bins",[{"model":model,"layer":l,"head":h,"score_bin":int(grid[l,h]),"bin_width":.02,"bin_min":-nb*.02,"selected":(l,h) in active,"source":source(model,"discovery/ranking.json")} for model,grid,active in zip(MODELS,bins,selected) for l in range(grid.shape[0]) for h in range(grid.shape[1])])
    render_localization_main(bins,selected,nb)
    render_localization_overlap_all(sets_by_model)
    # Retain full-precision appendix localization and layerwise maxima.
    color_max=max(float(np.abs(a).max()) for a in matrices);norm=TwoSlopeNorm(vmin=-color_max,vcenter=0,vmax=color_max)
    fig,axes=plt.subplots(2,3,figsize=(WIDE,4.32),gridspec_kw={"height_ratios":[1.65,1]});fig.subplots_adjust(left=.08,right=.985,bottom=.09,top=.79,wspace=.32,hspace=.54)
    for i,(model,matrix,active) in enumerate(zip(MODELS,matrices,selected)):
        ax=axes[0,i];im=ax.imshow(matrix,norm=norm,cmap="RdBu_r",interpolation="nearest",aspect="equal")
        for l,h in active:ax.add_patch(Rectangle((h-.5,l-.5),1,1,fill=False,ec=INK,lw=.45))
        ax.set(title=f"({chr(97+i)}) {MODEL_NAMES[model]}",xlabel="Head",xticks=np.arange(0,matrix.shape[1],8),yticks=np.arange(0,matrix.shape[0],8))
        if i==0:ax.set_ylabel("Layer")
        ax=axes[1,i];clean_axis(ax,"both",box=True);layers=np.arange(matrix.shape[0])
        ax.plot(layers,matrix.mean(axis=1),color=BLUE,marker="o",markersize=2.4,label="Mean")
        ax.plot(layers,matrix.max(axis=1),color=ORANGE,marker="s",markersize=2.4,label="Maximum")
        ax.set(xlabel="Layer",xticks=np.arange(0,matrix.shape[0],8),ylim=(-.04,color_max*1.13),title=f"({chr(100+i)})")
        if i==0:ax.set_ylabel("Attention gap")
    cb=fig.colorbar(im,cax=fig.add_axes([.22,.91,.56,.027]),orientation="horizontal");cb.ax.xaxis.set_ticks_position("top");cb.outline.set_visible(False)
    inset_legend(axes[1,0],"upper right")
    save_figure(fig,name)
    return profiles


def make_necessity():
    name="data_app_necessity";raw=[];measured_sizes={}
    for model in MODELS:
        filename=source(model,"causal_necessity/summary.json");data=read_json(filename);measured_sizes[model]=sorted(int(k) for k in data["controls"])
        for query in ("composed","direct_first","direct_target"):
            base=unique_record(data["summary"],method="native",query=query)
            raw.append({"model":model,"query":query,"selection":"native","knocked_out":0,"n":base["n"],"correct":base["correct"],"accuracy_percent":base["accuracy"]*100,"source":filename})
            for selection in ["selected","random"]:
                for size in measured_sizes[model]:
                    row=unique_record(data["summary"],method=f"{selection}_{size}",query=query)
                    raw.append({"model":model,"query":query,"selection":selection,"knocked_out":size,"n":row["n"],"correct":row["correct"],"accuracy_percent":100*row["accuracy"],"random_overlap_heads":data["controls"][str(size)]["overlap_heads"],"source":filename})
    export_csv(name,raw);render_necessity(raw,measured_sizes)
    return raw,measured_sizes


def make_ablation(seeds: list[int]) -> None:
    name="data_app_ablation";raw,aggregates=[],[]
    metrics=[("direct_first","core"),("all3","core"),("gsm8k","gsm8k")]
    for metric,dataset in metrics:
        for model in MODELS:
            for restored in (False,True):
                method=("scoped_body" if dataset=="core" else "final") if restored else "head_tuning"
                if metric=="all3":
                    values=[]
                    for seed in seeds:
                        filename=source(model,f"seed{seed}/evaluation/core/summary.json");row=unique_record(read_json(filename)["all3"],method=method)
                        values.append({"model":model,"seed":seed,"method":method,"dataset":dataset,"query":metric,"n":row["n"],"correct":row["correct"],"accuracy_percent":100*row["correct"]/row["n"],"metric":"accuracy","source":filename})
                else:values=seed_values(model,dataset,method,seeds,query=metric)
                for row in values:row["projection_restoration"]=restored
                raw.extend(values);mean,sd=mean_sd([row["accuracy_percent"] for row in values])
                aggregates.append({"model":model,"query":metric,"method":method,"projection_restoration":restored,"n_per_run":values[0]["n"],"runs":len(values),"mean_percent":mean,"sample_sd_percent":sd,"sources":";".join(row["source"] for row in values)})
    export_csv(f"{name}_seed_values",raw);export_csv(f"{name}_aggregated",aggregates);render_ablation(aggregates)


def make_capabilities(seeds: list[int]) -> None:
    name="data_app_capabilities";raw,aggregates=[],[]
    for dataset in ("hotpot","mmlu","gsm8k"):
        for model in MODELS:
            baseline=seed_values(model,dataset,"native",seeds);base=baseline[0]["accuracy_percent"]
            for method in ("native","fullft","final"):
                values=baseline if method=="native" else seed_values(model,dataset,method,seeds)
                raw.extend(values);mean,sd=mean_sd([row["accuracy_percent"] for row in values])
                aggregates.append({"dataset":dataset,"model":model,"method":method,"n_per_run":values[0]["n"],"recorded_runs":len(values),"native_percent":base,"mean_percent":mean,"sample_sd_percent":sd,"delta_pp":mean-base,"source_native":baseline[0]["source"],"sources":";".join(row["source"] for row in values)})
    export_csv(f"{name}_seed_values",raw);export_csv(f"{name}_aggregated",aggregates);render_capabilities(aggregates)


def make_ambiguity() -> None:
    filename="analysis/internal/ambiguous_evidence.json"
    rows=read_json(filename)["rows"]
    plotted=[{**r,"source":filename} for r in rows if r["method"] in ("graphfirst","final")]
    for m in MODELS:
        a=unique_record(plotted,model=m,method="graphfirst");b=unique_record(plotted,model=m,method="final")
        if a["n"]!=b["n"]:raise ValueError(f"Unmatched candidate-ranking populations: {m}")
    export_csv("data_main_ambiguity",plotted);render_ambiguity(plotted)



def make_case() -> None:
    filename="outputs/figures/worked_examples.json"
    cases=read_json(filename)
    record=unique_record(cases,model=MODELS[0])
    src=record["source"];pred=record["predictions"]
    native=unique_record(pred,method="native",query="composed")
    first=unique_record(pred,method="native",query="direct_first")
    second=unique_record(pred,method="native",query="direct_target")
    order=unique_record(pred,method="graphfirst",query="composed")
    reader=unique_record(pred,method="final",query="composed")
    graph=order["selection"]["graph"]
    assert graph==reader["selection"]["graph"] and len(graph["neighbors"])==2
    assert first["correct"] and second["correct"] and not native["correct"]
    assert not order["correct"] and reader["correct"]
    context=src["original_context"]
    assert context[reader["selection"]["chosen"]][0]==src["bridge"]
    # Colors mark the recorded choices, not token-level attribution values.
    rows=[]
    for label,prediction in [("Input order",order),("Full reader",reader)]:
        chosen=prediction["selection"]["chosen"]
        rows.append({"model":record["model"],"source_id":record["source_id"],"policy":label,
                     "root":src["root"],"question":src["original_question"],"gold":src["original_gold"],
                     "chosen":chosen,"candidate":context[chosen][0],"answer":prediction["answer"],
                     "correct":prediction["correct"],"source":filename})
    export_csv("data_main_case",rows)
    fig,ax=plt.subplots(figsize=(COL,1.78));fig.subplots_adjust(left=.025,right=.975,bottom=.025,top=.99)
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis("off")
    def put(x,y,string,**kw):
        ax.text(x,y,string,ha="left",va="top",**kw)
    def box(x,y,w,h,color):
        ax.add_patch(Rectangle((x,y),w,h,facecolor=color,edgecolor="#D3D6DA",linewidth=.45))
    put(.005,.99,"Q: "+textwrap.fill(src["original_question"],68),fontsize=6.0,fontweight="medium")
    put(.005,.775,"Native answer: "+native["answer"],fontsize=5.6,color="#4D5054")
    put(.005,.699,"Linked candidate paragraphs",fontsize=5.6,fontweight="bold")
    for row,y,color in zip(rows,(.365,.045),("#EEF2F8","#FBEEE5")):
        box(.005,y,.99,.275,color)
        title=textwrap.fill(row["candidate"],64)
        put(.026,y+.250,f"P{row['chosen']}: "+title,fontsize=5.55)
        put(.026,y+.096,row["policy"]+"  \N{RIGHTWARDS ARROW}  "+row["answer"],fontsize=5.9,fontweight="bold",color=BLUE if not row["correct"] else "#A65D38")
    save_figure(fig,"data_main_case")


def render_mechanism_cases(cases):
    """Display recorded answers and literal evidence excerpts, never activation maps."""
    corvinus,angela=cases["corvinus"],cases["angela"]
    fig=plt.figure(figsize=(WIDE,2.50))
    left=fig.add_axes([.018,.025,.472,.95])
    right=fig.add_axes([.522,.025,.46,.95])
    for ax in (left,right):
        ax.set(xlim=(0,1),ylim=(0,1));ax.axis("off")
    fig.add_artist(Line2D([.504,.504],[.045,.965],transform=fig.transFigure,
                          color="#C7CCD1",linewidth=.6))

    def put(ax,x,y,string,width=None,**kwargs):
        if width is not None:
            string=textwrap.fill(string,width=width,break_long_words=False,
                                 break_on_hyphens=False)
        settings=dict(ha="left",va="top",fontsize=6.2,linespacing=1.05,color=INK)
        settings.update(kwargs)
        return ax.text(x,y,string,**settings)

    # Case A uses the canonical test context. The answers are identical in the
    # three archived model records, so one shared column avoids repetition.
    put(left,.01,.995,"(a) Correct hops, failed composition",fontsize=7.1,fontweight="bold")
    put(left,.01,.932,"All three models · canonical test context",fontsize=6.0,color="#555D66")
    put(left,.01,.858,"Q: "+corvinus["question"],width=73,fontsize=6.35,fontweight="medium")
    put(left,.01,.765,"Supplied evidence (excerpts)",fontsize=6.15,fontweight="bold")
    first,second=corvinus["evidence"]
    # Preserve literal source spans and mark every omitted span with ellipses.
    first_clause=first["text"].split(") ",1)[1]
    first_clause=first_clause[:first_clause.index(first["object"])+len(first["object"])]
    second_clause=second["text"].split(",",1)[0]
    put(left,.025,.710,first["title"],fontweight="bold",color=BLUE)
    put(left,.025,.666,"“... "+first_clause+" ...”",width=77)
    put(left,.025,.589,second["title"],fontweight="bold",color=BLUE)
    put(left,.025,.545,"“"+second_clause+" ...”",width=77)

    put(left,.01,.445,"Recorded answers",fontsize=6.15,fontweight="bold")
    one=corvinus["model_results"][0]
    outcomes=[("Native · first hop",one["native_answers"]["direct_first"]),
              ("Native · second hop",one["native_answers"]["direct_target"]),
              ("Native · composed",one["native_answers"]["composed"]),
              ("CoReTrace · composed",one["coretrace_composed"])]
    for y,(label,record) in zip((.354,.263,.172,.081),outcomes):
        fill="#F2F4F6" if label.startswith("Native") else "#E8F2EC"
        if not record["correct"]:fill="#FBEEE9"
        left.add_patch(Rectangle((.005,y-.048),.99,.083,facecolor=fill,
                                 edgecolor="none",zorder=0))
        put(left,.025,y+.019,label,fontsize=6.25)
        put(left,.52,y+.019,record["answer"],fontsize=6.5,fontweight="bold",
            color="#307653" if record["correct"] else "#A74738")

    # Case B keeps the native-model four-arm diagnostic distinct from the
    # complete repaired system's response to a reciprocal fact exchange.
    put(right,.01,.995,"(b) Access-dependent local reading",fontsize=7.1,fontweight="bold")
    put(right,.01,.932,"Llama-3.1-8B · shared-context diagnostic",fontsize=6.0,color="#555D66")
    put(right,.01,.858,"Q: "+angela["question"],width=72,fontsize=6.3,fontweight="medium")
    put(right,.01,.755,"Supplied evidence (excerpts)",fontsize=6.15,fontweight="bold")
    first,second=angela["evidence"]
    film_clause=first["text"].split(" and starring",1)[0]
    parent_prefix=second["text"].split(",",1)[0]
    parent_suffix="and his third wife"+second["text"].split("and his third wife",1)[1].split(",",1)[0]
    put(right,.025,.708,"“"+film_clause+" ...”",width=74)
    put(right,.025,.648,"“"+parent_prefix+" ... "+parent_suffix+" ...”",width=74)
    put(right,.01,.523,"Attention intervention in the native model",fontsize=6.15,fontweight="bold")
    arms={row["method"]:row for row in angela["diagnostic"]["arms"]}
    slots=(("native","Native",.005,.365),("conditional_only","Pattern only",.51,.365),
           ("mass_only","Mass only",.005,.250),("both","Both",.51,.250))
    for key,label,x,y in slots:
        record=arms[key]
        right.add_patch(Rectangle((x,y),.48,.105,
                                  facecolor="#E8F2EC" if record["correct"] else "#F2F4F6",
                                  edgecolor="#C9CED3",linewidth=.45))
        put(right,x+.018,y+.090,label,fontsize=6.0,color="#555D66")
        put(right,x+.018,y+.048,record["answer"],fontsize=6.35,fontweight="bold",
            color="#307653" if record["correct"] else INK)

    exchange=angela["fact_exchange"]
    put(right,.01,.214,"CoReTrace on a reciprocal fact exchange",fontsize=6.15,fontweight="bold")
    put(right,.025,.160,"Mother names: "+exchange["original_gold"]+"  ↔  "+exchange["edited_gold"],fontsize=6.1)
    put(right,.025,.108,"Answers:",fontsize=6.2)
    put(right,.225,.108,exchange["original"]["answer"]+"  →  "+exchange["edited"]["answer"],
        fontsize=6.5,fontweight="bold",color="#307653")
    selected=exchange["original"]["selected_paragraph"]
    selected_fact=next(row for row in exchange["exchanged_facts"] if row["paragraph_index"]==selected)
    put(right,.025,.047,"Same selected paragraph: "+selected_fact["title"],fontsize=6.0,color="#555D66")
    save_figure(fig,"data_main_mechanism_cases")


def make_mechanism_cases() -> None:
    filename="analysis/internal/mechanism_case_records_20261125_v2.json"
    data=read_json(filename);cases=data["cases"]
    corvinus,angela=cases["corvinus"],cases["angela"]
    results=corvinus["model_results"]
    if {row["model"] for row in results}!=set(MODELS):
        raise ValueError("The cross-model case must retain all three recorded models")
    shared=[]
    traces=[]
    for row in results:
        answers=row["native_answers"]
        if not (answers["direct_first"]["correct"] and answers["direct_target"]["correct"]
                and not answers["composed"]["correct"] and row["coretrace_composed"]["correct"]):
            raise ValueError("The canonical case no longer has the displayed outcome pattern")
        shared.append(tuple(answers[key]["answer"] for key in ("direct_first","direct_target","composed"))
                      +(row["coretrace_composed"]["answer"],))
        for key in ("direct_first","direct_target","composed"):
            traces.append(("corvinus",row["model"],"native",key,"original",answers[key]))
        traces.append(("corvinus",row["model"],"coretrace","composed","original",row["coretrace_composed"]))
    if len(set(shared))!=1:
        raise ValueError("A shared answer column requires identical answers across all three models")
    if shared[0][0]!=shared[0][2]:
        raise ValueError("The displayed composition failure must repeat the recorded first-hop answer")
    diagnostic=angela["diagnostic"];exchange=angela["fact_exchange"]
    if not all(diagnostic["checks"].values()) or not all(exchange["checks"].values()):
        raise ValueError("Mechanistic case context-alignment checks must all pass")
    if not exchange["original"]["correct"] or not exchange["edited"]["correct"]:
        raise ValueError("The repaired answers must follow both recorded fact versions")
    if exchange["original"]["selected_paragraph"]!=exchange["edited"]["selected_paragraph"]:
        raise ValueError("The displayed fact exchange must retain the selected paragraph")
    for row in diagnostic["arms"]:
        if row["source_id"]!=angela["source_id"] or row["correct"]!=(row["method"]=="both"):
            raise ValueError("Four-arm source identity or displayed answer outcomes disagree")
        traces.append(("angela",diagnostic["model"],"attention_intervention",row["method"],"original",row))
    for view in ("original","edited"):
        traces.append(("angela",exchange["model"],"coretrace_fact_exchange","composed",view,exchange[view]))
    export_csv("data_main_mechanism_cases_trace",[
        {"case":case,"model":model,"population":cases[case]["population"],
         "source_id":record["source_id"],"receiver_id":record["id"],
         "procedure":procedure,"condition":condition,"view":view,
         "answer":record["answer"],"correct":record["correct"],
         "selected_paragraph":record.get("selected_paragraph",record.get("selection",{}).get("chosen")),
         "prediction_source":";".join(record["source_path"]) if isinstance(record["source_path"],list) else record["source_path"],
         "case_record_source":filename}
        for case,model,procedure,condition,view,record in traces])
    render_mechanism_cases(cases)


V3_STYLE = {"font.size":6.2, "axes.labelsize":6.4, "axes.titlesize":6.6,
            "xtick.labelsize":6.0, "ytick.labelsize":6.0,
            "legend.fontsize":6.1}


def make_mechanism_causality() -> None:
    """Reuse recorded knockout outcomes without rewriting earlier exports."""
    filename="analysis/figure_data/data_app_necessity.csv"
    INPUT_PATHS.add(filename)
    with (ROOT/filename).open(newline="",encoding="utf-8") as handle:
        existing=list(csv.DictReader(handle))
    rows=[]
    for row in existing:
        if row["query"] not in {"composed","direct_target"}:
            continue
        record={**row,"derived_input":filename}
        for key in ("knocked_out","n","correct"):
            record[key]=int(row[key])
        record["accuracy_percent"]=float(row["accuracy_percent"])
        if row.get("random_overlap_heads"):
            record["random_overlap_heads"]=int(row["random_overlap_heads"])
        if not np.isclose(record["accuracy_percent"],100*record["correct"]/record["n"]):
            raise ValueError(f"Inconsistent knockout numerator: {record}")
        rows.append(record)
    for model in MODELS:
        for query in ("composed","direct_target"):
            unique_record(rows,model=model,query=query,selection="native")
            for selection in ("selected","random"):
                for size in (20,40,80):
                    unique_record(rows,model=model,query=query,selection=selection,knocked_out=size)
    export_csv("data_main_head_causality",rows)
    render_mechanism_causality(rows)


def render_mechanism_causality(rows) -> None:
    """Show the measured necessity curves for paired endpoint questions."""
    with plt.rc_context(V3_STYLE):
        fig,axes=plt.subplots(2,3,figsize=(WIDE,2.85),sharex=True,sharey="row")
        fig.subplots_adjust(left=.075,right=.985,bottom=.155,top=.825,
                            wspace=.20,hspace=.28)
        for col,model in enumerate(MODELS):
            for row_index,query in enumerate(("composed","direct_target")):
                ax=axes[row_index,col]
                clean_axis(ax)
                base=unique_record(rows,model=model,query=query,selection="native")
                baseline=base["accuracy_percent"]
                ax.axhline(baseline,color=INK,linestyle=(0,(3,2)),linewidth=.7,
                           label="Native baseline",zorder=1)
                for selection,label,color,marker in (
                        ("selected","Ranked heads",MODEL_COLORS[col],"o"),
                        ("random","Layer-matched random",GRAY,"s")):
                    selected=sorted([r for r in rows if r["model"]==model and
                                     r["query"]==query and r["selection"]==selection],
                                    key=lambda r:r["knocked_out"])
                    x=[0]+[r["knocked_out"] for r in selected]
                    y=[baseline]+[r["accuracy_percent"] for r in selected]
                    ax.plot(x,y,color=color,marker=marker,markersize=3.4,
                            markeredgecolor="white",markeredgewidth=.35,
                            linewidth=1.2,label=label,zorder=4 if selection=="selected" else 3)
                ax.set(xticks=[0,20,40,80],xlim=(-3,83))
                if row_index==0:
                    ax.set_title(MODEL_NAMES[model],fontsize=6.7,pad=5)
                    ax.set(ylim=(0,41),yticks=[0,20,40])
                else:
                    ax.set(ylim=(0,65),yticks=[0,20,40,60],xlabel="Heads removed")
                if col==0:
                    ax.set_ylabel("Composed EM (%)" if row_index==0 else "Direct-target EM (%)",
                                  fontsize=6.3,labelpad=4)
                ax.tick_params(labelsize=6.0)
                ax.text(.00,1.015,f"({chr(97+row_index*3+col)})",transform=ax.transAxes,
                        ha="left",va="bottom",fontsize=6.2,color=INK)
        handles,labels=axes[0,0].get_legend_handles_labels()
        order=[1,2,0]
        fig.legend([handles[i] for i in order],[labels[i] for i in order],
                   loc="upper center",bbox_to_anchor=(.54,.985),ncol=3,frameon=False,
                   fontsize=6.2,handlelength=2.1,columnspacing=1.7,handletextpad=.55)
        save_figure(fig,"data_main_head_causality")


def make_joint_rescue() -> None:
    """Partition recorded Both repairs by the two single-intervention outcomes."""
    filename="analysis/internal/v3_causal_evidence.json"
    data=read_json(filename)
    rows=[]
    plotted=[]
    for model in MODELS:
        record=data["factorial"][model]
        summary=record["summary"]
        cells=record["native_failure_both_success_2x2"]
        if len(cells)!=4 or len({(r["mass_correct"],r["pattern_correct"]) for r in cells})!=4:
            raise ValueError(f"Joint-rescue partition is not a complete 2-by-2 table: {model}")
        total=sum(r["n"] for r in cells)
        if total!=summary["both_rescues_native_failure"]:
            raise ValueError(f"Joint-rescue cells do not sum to Both repairs: {model}")
        joint=unique_record(cells,mass_correct=False,pattern_correct=False)["n"]
        if joint!=summary["joint_only_rescue"]:
            raise ValueError(f"Joint-only repair count disagrees with receiver summary: {model}")
        receiver_ids=[]
        for cell in cells:
            if cell["n"]!=len(cell["source_ids"]) or cell["n"]!=len(cell["receiver_ids"]):
                raise ValueError(f"Joint-rescue count and source IDs disagree: {model}")
            receiver_ids.extend(cell["receiver_ids"])
            rows.append({"model":model,"mass_correct":cell["mass_correct"],
                         "pattern_correct":cell["pattern_correct"],"count":cell["n"],
                         "both_repairs":total,"native_failures":summary["native_failures"],
                         "receiver_population":summary["n"],"quadruplets":summary["quadruplets"],
                         "source_ids":";".join(cell["source_ids"]),
                         "receiver_ids":";".join(cell["receiver_ids"]),"source":filename})
        if len(set(receiver_ids))!=total:
            raise ValueError(f"A receiver appears in more than one joint-rescue cell: {model}")
        for group,count in (("both_required",joint),("at_least_one_single_succeeds",total-joint)):
            plotted.append({"model":model,"group":group,"count":count,
                            "both_repairs":total,"native_failures":summary["native_failures"],
                            "share_of_native_failures_percent":100*count/summary["native_failures"],
                            "share_of_both_repairs_percent":100*count/total,"source":filename})
    export_csv("data_main_joint_rescue",rows)
    export_csv("data_main_joint_rescue_plotted",plotted)
    render_joint_rescue(plotted)


def render_joint_rescue(rows) -> None:
    with plt.rc_context(V3_STYLE):
        fig,ax=plt.subplots(figsize=(COL,1.90))
        fig.subplots_adjust(left=.30,right=.94,bottom=.25,top=.72)
        clean_axis(ax,"x")
        ys=np.arange(len(MODELS))[::-1]
        largest=max(row["both_repairs"] for row in rows)
        for i,(y,model) in enumerate(zip(ys,MODELS)):
            joint=unique_record(rows,model=model,group="both_required")
            other=unique_record(rows,model=model,group="at_least_one_single_succeeds")
            ax.barh(y,joint["count"],height=.57,color=MODEL_COLORS[i],
                    edgecolor="white",linewidth=.7,zorder=3,
                    label="Both required" if i==0 else None)
            ax.barh(y,other["count"],left=joint["count"],height=.57,
                    color=LIGHT_GRAY,edgecolor="white",linewidth=.7,zorder=3,
                    label="A single arm also succeeds" if i==0 else None)
            for count,left,color in ((joint["count"],0,"white"),
                                     (other["count"],joint["count"],INK)):
                if count:
                    ax.text(left+count/2,y,str(count),ha="center",va="center",
                            color=color,fontsize=6.5,fontweight="bold")
            ax.text(joint["both_repairs"]+.55,y,str(joint["both_repairs"]),
                    ha="left",va="center",fontsize=6.2,color=INK)
        ax.set(yticks=ys,yticklabels=[f"{MODEL_NAMES[m]}\n$n={unique_record(rows,model=m,group='both_required')['native_failures']}$ failures"
                                     for m in MODELS],
               ylim=(-.6,len(MODELS)-.4),xlim=(0,largest+3.2),
               xticks=list(range(0,int(largest)+2,10)),
               xlabel="Native failures corrected by Both (count)")
        ax.spines[["top","right","left"]].set_visible(False)
        ax.tick_params(axis="y",length=0,pad=4,labelsize=6.0)
        ax.tick_params(axis="x",labelsize=6.0)
        ax.xaxis.label.set_size(6.0)
        handles,labels=ax.get_legend_handles_labels()
        fig.legend(handles,labels,loc="upper center",bbox_to_anchor=(.57,.985),
                   ncol=1,frameon=False,fontsize=6.0,handlelength=1.3,
                   handletextpad=.45,labelspacing=.45)
        save_figure(fig,"data_main_joint_rescue")


def make_address_routing() -> None:
    """Connect a native address signal, measured allocation, and recorded repair."""
    filename="analysis/internal/v3_causal_evidence.json"
    data=read_json(filename)
    if data.get("status")!="COMPLETE":
        raise ValueError("Address-routing requires the completed, source-joined evidence export")
    previous="analysis/figure_data/data_fig4_causal_access_controls.csv"
    INPUT_PATHS.add(previous)
    with (ROOT/previous).open(newline="",encoding="utf-8") as handle:
        access=list(csv.DictReader(handle))
    for row in access:
        for field in ("n","native_correct","intervened_correct","clusters"):
            row[field]=int(row[field])
        for field in ("delta_pp","CI95_low_pp","CI95_high_pp"):
            row[field]=float(row[field])
        row["derived_input"]=previous
        all_sources=unique_record(data["address_access"][row["model"]]["subgroups"],name="all")
        if (row["n"]!=all_sources["n"] or
                row["native_correct"]!=all_sources["conditions"]["native"]["correct"] or
                row["intervened_correct"]!=all_sources["conditions"][row["method"]]["correct"]):
            raise ValueError(f"Original destination control and source-joined records disagree: {row}")
    conditional=[]
    masses=[]
    subgroup="full_decoded_known_constituents_native_failure"
    methods=("oracle_second_paragraph","oracle_first_paragraph","lengthmatched_other_paragraph")
    for model in MODELS:
        group=unique_record(data["address_access"][model]["subgroups"],name=subgroup)
        if group["native_correct"]!=0 or group["n"]!=len(set(group["source_ids"])):
            raise ValueError(f"Invalid fixed native-failure subgroup: {model}")
        for method in methods:
            outcome=group["conditions"][method]
            low,high=outcome["source_bootstrap_CI95_percent"]
            if (outcome["correct"]!=outcome["rescued_from_native"] or
                    not np.isclose(outcome["accuracy_percent"],100*outcome["correct"]/group["n"])):
                raise ValueError(f"Conditional repair numerator disagrees: {model}/{method}")
            conditional.append({"model":model,"method":method,"subgroup":subgroup,
                                "n":group["n"],"corrected":outcome["correct"],
                                "repair_percent":outcome["accuracy_percent"],
                                "CI95_low_percent":low,"CI95_high_percent":high,
                                "bootstrap_reps":group["source_bootstrap"]["reps"],
                                "bootstrap_seed":group["source_bootstrap"]["seed"],
                                "bootstrap_unit":group["source_bootstrap"]["unit"],
                                "source_ids":";".join(group["source_ids"]),"source":filename})
        means=group["native_paragraph_mass_means"]["all_question_mean"]
        for role in ("root","bridge"):
            masses.append({"model":model,"subgroup":subgroup,"n":group["n"],
                           "role":role,"question_rows":"all_question_mean",
                           "attention_mass_percent":100*means[role],
                           "root_exceeds_bridge_count":group["native_root_exceeds_bridge_count"],
                           "source":filename})
    export_csv("data_main_address_routing_all_sources",access)
    export_csv("data_main_address_routing_conditional",conditional)
    export_csv("data_main_address_routing_mass",masses)
    render_address_routing(access,masses,conditional)


def render_address_routing(access,masses,conditional) -> None:
    with plt.rc_context(V3_STYLE):
        fig,axes=plt.subplots(1,3,figsize=(WIDE,2.40))
        fig.subplots_adjust(left=.065,right=.985,bottom=.265,top=.775,wspace=.38)
        x=np.arange(len(MODELS));width=.23
        specs=(("oracle_second_paragraph","Bridge",BLUE),
               ("oracle_first_paragraph","Root",ORANGE),
               ("lengthmatched_other_paragraph","Other",GRAY))
        for ax in axes:
            clean_axis(ax)
            ax.tick_params(labelsize=6.0)
            ax.set_xlim(-.55,2.55)
        for j,(method,label,color) in enumerate(specs):
            pos=x+(j-1)*width
            source_rows=[unique_record(access,model=m,method=method) for m in MODELS]
            values=np.array([r["delta_pp"] for r in source_rows])
            low=np.array([r["CI95_low_pp"] for r in source_rows])
            high=np.array([r["CI95_high_pp"] for r in source_rows])
            axes[0].bar(pos,values,width,color=color,edgecolor=INK,linewidth=.4,
                        zorder=3,label=label)
            axes[0].errorbar(pos,values,yerr=[values-low,high-values],fmt="none",
                            ecolor=INK,elinewidth=.7,capsize=1.7,capthick=.7,zorder=4)
            repair_rows=[unique_record(conditional,model=m,method=method) for m in MODELS]
            repair=np.array([r["repair_percent"] for r in repair_rows])
            lower=np.array([r["CI95_low_percent"] for r in repair_rows])
            upper=np.array([r["CI95_high_percent"] for r in repair_rows])
            axes[2].bar(pos,repair,width,color=color,edgecolor=INK,linewidth=.4,zorder=3)
            axes[2].errorbar(pos,repair,yerr=[repair-lower,upper-repair],fmt="none",
                            ecolor=INK,elinewidth=.7,capsize=1.7,capthick=.7,zorder=4)
            for xpos,row,limit in zip(pos,repair_rows,upper):
                axes[2].text(xpos,limit+1.0,str(row["corrected"]),ha="center",va="bottom",
                             fontsize=6.0,color=INK)
        for j,(role,color) in enumerate((("root",ORANGE),("bridge",BLUE))):
            values=[unique_record(masses,model=m,role=role)["attention_mass_percent"] for m in MODELS]
            axes[1].bar(x+(j-.5)*.30,values,.30,color=color,edgecolor=INK,
                        linewidth=.4,zorder=3)
        axes[0].axhline(0,color=INK,linewidth=.65)
        axes[0].set(ylim=(-27,25),yticks=[-20,0,20],ylabel="EM change (pp)",
                    xticks=x,xticklabels=[SHORT[m] for m in MODELS])
        axes[1].set(ylim=(0,38),yticks=[0,10,20,30],ylabel="Question-row mass (%)")
        axes[2].set(ylim=(0,61),yticks=[0,20,40,60],ylabel="Composition failures repaired (%)")
        labels=[f"{SHORT[m]}\n$n={unique_record(masses,model=m,role='root')['n']}$" for m in MODELS]
        for ax in axes[1:]:
            ax.set(xticks=x,xticklabels=labels)
        titles=("(a) Destination controls","(b) Native allocation","(c) Routing repair")
        subtitles=("1,000 test sources","Decoded native failures","Same failures; labels = count")
        for ax,title,subtitle in zip(axes,titles,subtitles):
            ax.set_title(title,fontsize=6.8,pad=17,fontweight="bold")
            ax.text(.5,1.055,subtitle,transform=ax.transAxes,ha="center",va="bottom",
                    fontsize=6.0,color="#555D66")
            ax.yaxis.label.set_size(6.2)
        handles,legend_labels=axes[0].get_legend_handles_labels()
        fig.legend(handles,legend_labels,loc="upper center",bbox_to_anchor=(.54,1.0),
                   ncol=3,frameon=False,fontsize=6.2,handlelength=1.3,
                   columnspacing=1.8,handletextpad=.5)
        save_figure(fig,"data_main_address_routing")


def make_mechanism_structure() -> None:
    """Expose head membership and the recorded paragraph allocation it indexes."""
    filename="analysis/internal/v3_structure_evidence.json"
    data=read_json(filename)
    overlaps=[];profiles=[];source_profiles=[]
    for model in MODELS:
        record=data["models"][model]
        for cell in record["exact_intersections"]:
            overlaps.append({"model":model,"k":record["k"],**cell,"source":filename})
        for group in ("selected","random_layer_matched"):
            group_record=record["aggregate_profiles"][group]
            metric=group_record["metrics"]["all_question_mean"]
            n=len(metric["source_ids"])
            if n!=record["n_sources"]:
                raise ValueError(f"Structure source count disagrees: {model}/{group}")
            for query in ("composed","direct_target"):
                means=metric["means_by_query"][query]
                measurements=metric["per_source"][query]
                for role in ("root","bridge","distractor_mean","distractor_sum"):
                    if len(measurements[role])!=n or not np.isclose(np.mean(measurements[role]),means[role]):
                        raise ValueError(f"Structure mean disagrees with sources: {model}/{group}/{query}/{role}")
                profiles.append({"model":model,"head_set":group,"query":query,
                                 "n_sources":n,"n_heads":group_record["n_heads"],
                                 "question_rows":"all_question_mean",
                                 "root_mass_percent":100*means["root"],
                                 "bridge_mass_percent":100*means["bridge"],
                                 "distractor_mean_percent":100*means["distractor_mean"],
                                 "distractor_sum_percent":100*means["distractor_sum"],
                                 "bridge_minus_root_pp":100*(means["bridge"]-means["root"]),
                                 "source":filename})
                for index,source_id in enumerate(metric["source_ids"]):
                    source_profiles.append({"model":model,"head_set":group,"query":query,
                                            "source_id":source_id,"n_heads":group_record["n_heads"],
                                            "question_rows":"all_question_mean",
                                            "root_mass_percent":100*measurements["root"][index],
                                            "bridge_mass_percent":100*measurements["bridge"][index],
                                            "distractor_mean_percent":100*measurements["distractor_mean"][index],
                                            "distractor_sum_percent":100*measurements["distractor_sum"][index],
                                            "source":filename})
    # These are audited discovery examples. IDs select records; all text,
    # attention values, head IDs, and intervention outcomes come from the export.
    example_ids=(("qwen3_4b","6a0c11720bdb11eba7f7acde48001122"),
                 ("llama3_8b","d3c5124a0bda11eba7f7acde48001122"))
    examples=[];head_rows=[];example_rows=[]
    for model,source_id in example_ids:
        record=data["models"][model]
        example=unique_record(record["representative_candidates"],source_id=source_id)
        primary=record["primary_head"]
        head=unique_record(example["heads"],layer=primary["layer"],head=primary["head"])
        calibration=example["canonical_mass_calibration"]
        if (not head["selected"] or calibration["selected_head_count"]!=record["k"] or
                calibration["native"]["correct"] or not calibration["calibrated"]["correct"]):
            raise ValueError(f"Displayed head/set intervention is inconsistent: {model}/{source_id}")
        for query in ("composed","direct_target"):
            question=example["questions"][query]
            if question["source_id"]!=source_id:
                raise ValueError(f"Head portrait has a different query source: {model}/{source_id}")
            masses=head["paragraph_mass"][query]["all_question_mean"]
            if len(masses)!=len(example["paragraph_titles"]) or not all(0<=value<=1 for value in masses):
                raise ValueError(f"Invalid paragraph mass vector: {model}/{source_id}/{query}")
            for index,(title,value) in enumerate(zip(example["paragraph_titles"],masses)):
                role="root" if index==example["root_index"] else "bridge" if index==example["bridge_index"] else "distractor"
                head_rows.append({"model":model,"source_id":source_id,"query":query,
                                  "question":question["question"],"layer":head["layer"],"head":head["head"],
                                  "paragraph_index":index,"paragraph_title":title,"role":role,
                                  "question_rows":"all_question_mean","attention_mass_percent":100*value,
                                  "source":filename})
        for arm in ("native","calibrated"):
            result=calibration[arm]
            example_rows.append({"model":model,"source_id":source_id,"condition":arm,
                                 "answer":result["answer"],"correct":result["correct"],
                                 "selected_head_count":calibration["selected_head_count"],
                                 "displayed_layer":head["layer"],"displayed_head":head["head"],
                                 "intervention_scope":"selected_head_set" if arm=="calibrated" else "native",
                                 "root_index":example["root_index"],"bridge_index":example["bridge_index"],
                                 "source":filename})
        examples.append({"model":model,"record":example,"head":head})
    export_csv("data_main_structure_function_overlap",overlaps)
    export_csv("data_main_structure_function_profiles",profiles)
    export_csv("data_main_structure_function_source_profiles",source_profiles)
    export_csv("data_main_structure_function_heads",head_rows)
    export_csv("data_main_structure_function_examples",example_rows)
    render_mechanism_structure(data,overlaps,profiles,examples)


def render_mechanism_structure(data,overlaps,profiles,examples) -> None:
    with plt.rc_context(V3_STYLE):
        fig=plt.figure(figsize=(WIDE,3.00))
        fig.text(.025,.985,"(a) Head-set structure",ha="left",va="top",fontsize=7.0,fontweight="bold")
        model=MODELS[0]
        k=data["models"][model]["k"]
        fig.text(.025,.915,f"{MODEL_NAMES[model]} · $k={k}$",ha="left",va="top",fontsize=6.2)
        intersections=sorted([r for r in overlaps if r["model"]==model and r["count"]>0],
                             key=lambda r:(-r["count"],-r["selected"],-r["direct"],-r["composed"]))
        counts=[r["count"] for r in intersections]
        x=np.arange(len(counts))
        top=fig.add_axes([.151,.715,.185,.165])
        clean_axis(top)
        top.bar(x,counts,width=.68,color=INK,zorder=3)
        for xpos,count in zip(x,counts):
            top.text(xpos,count+.35,str(count),ha="center",va="bottom",fontsize=6.0)
        top.set(xlim=(-.55,len(counts)-.45),ylim=(0,max(counts)+5),yticks=[0,10,20],ylabel="Heads")
        top.tick_params(axis="x",bottom=False,labelbottom=False)
        top.tick_params(axis="y",labelsize=6.0)
        top.yaxis.label.set_size(6.0)
        membership=fig.add_axes([.151,.555,.185,.115])
        membership.set(xlim=top.get_xlim(),ylim=(2.5,-.5),xticks=[],yticks=[0,1,2],
                       yticklabels=["Selected","Direct top-k","Composed top-k"])
        for j,row in enumerate(intersections):
            active=[]
            for y,key in enumerate(("selected","direct","composed")):
                membership.plot(j,y,"o",color=INK if row[key] else "#D6D9DD",markersize=3.9)
                if row[key]:active.append(y)
            if len(active)>1:
                membership.plot([j,j],[min(active),max(active)],color=INK,linewidth=.8,zorder=0)
        membership.tick_params(length=0,pad=3,labelsize=6.0)
        for spine in membership.spines.values():spine.set_visible(False)

        fig.text(.410,.985,"(b) Root-to-bridge preference",ha="left",va="top",fontsize=7.0,fontweight="bold")
        preference=fig.add_axes([.492,.605,.470,.270])
        clean_axis(preference,"x")
        all_values=[]
        for i,model in enumerate(MODELS):
            y=len(MODELS)-1-i
            for group,offset,color,style in (("selected",.12,MODEL_COLORS[i],"-"),
                                           ("random_layer_matched",-.12,GRAY,"--")):
                points=[unique_record(profiles,model=model,head_set=group,query=q)["bridge_minus_root_pp"]
                        for q in ("composed","direct_target")]
                all_values.extend(points)
                preference.plot(points,[y+offset]*2,linestyle=style,color=color,linewidth=1.1,zorder=3)
                preference.plot(points[0],y+offset,marker="o",markersize=3.8,
                                markerfacecolor="white",markeredgecolor=color,markeredgewidth=1,zorder=4)
                preference.plot(points[1],y+offset,marker="o",markersize=3.8,
                                markerfacecolor=color,markeredgecolor=color,markeredgewidth=.7,zorder=4)
        preference.axvline(0,color=GRAY,linewidth=.6,zorder=1)
        limit_low=5*np.floor((min(all_values)-3)/5)
        limit_high=5*np.ceil((max(all_values)+3)/5)
        preference.set(yticks=[2,1,0],yticklabels=[MODEL_NAMES[m] for m in MODELS],
                       ylim=(-.5,2.5),xlim=(limit_low,limit_high),xlabel="Bridge − root mass (pp)")
        preference.set_xticks(np.arange(np.ceil(limit_low/10)*10,limit_high+1,10))
        preference.tick_params(axis="y",length=0,pad=4,labelsize=6.0)
        preference.tick_params(axis="x",labelsize=6.0)
        preference.xaxis.label.set_size(6.1)
        preference.spines["left"].set_visible(False)
        handles=[Line2D([],[],marker="o",linestyle="none",color=INK,markerfacecolor="white",markersize=3.7),
                 Line2D([],[],marker="o",linestyle="none",color=INK,markersize=3.7),
                 Line2D([],[],color=INK,linewidth=1.1),
                 Line2D([],[],color=GRAY,linestyle="--",linewidth=1.1)]
        fig.legend(handles,["Composed","Direct","Selected","Matched random"],
                   loc="upper center",bbox_to_anchor=(.710,.945),ncol=4,frameon=False,
                   fontsize=6.0,handlelength=1.3,handletextpad=.35,columnspacing=.8)

        matrices=[]
        for example in examples:
            matrices.append(100*np.array([example["head"]["paragraph_mass"][q]["all_question_mean"]
                                          for q in ("composed","direct_target")]))
        maximum=10*np.ceil(max(float(matrix.max()) for matrix in matrices)/10)
        norm=matplotlib.colors.Normalize(vmin=0,vmax=maximum)
        for index,(example,matrix,left) in enumerate(zip(examples,matrices,(.035,.545))):
            model=example["model"];record=example["record"];head=example["head"]
            fig.text(left,.443,
                     f"({chr(99+index)}) {MODEL_NAMES[model]} · L{head['layer']}H{head['head']} · mass (%)",
                     ha="left",va="top",fontsize=6.7,fontweight="bold")
            questions=[]
            for prefix,query in (("q12","composed"),("q2","direct_target")):
                questions.append(textwrap.fill(prefix+": "+record["questions"][query]["question"],
                                                width=75,subsequent_indent="    ",
                                                break_long_words=False,break_on_hyphens=False))
            fig.text(left,.397,"\n".join(questions),ha="left",va="top",fontsize=6.0,
                     linespacing=1.08,color=INK)
            ax=fig.add_axes([left+.045,.180,.400,.100])
            ax.imshow(matrix,cmap="Blues",norm=norm,aspect="auto",interpolation="nearest")
            for row in range(matrix.shape[0]):
                for col in range(matrix.shape[1]):
                    value=matrix[row,col]
                    ax.text(col,row,f"{value:.1f}",ha="center",va="center",fontsize=6.0,
                            color="white" if value>maximum*.55 else INK)
            for key,color in (("root_index",ORANGE),("bridge_index",BLUE)):
                ax.add_patch(Rectangle((record[key]-.5,-.5),1,2,fill=False,
                                       edgecolor=color,linewidth=1.35))
            ax.set(xticks=np.arange(matrix.shape[1]),xticklabels=[f"P{i}" for i in range(matrix.shape[1])],
                   yticks=[0,1],yticklabels=["q12","q2"])
            ax.tick_params(axis="both",length=0,pad=2,labelsize=6.0)
            for spine in ax.spines.values():spine.set_visible(False)
            role_text=(f"Root P{record['root_index']}: {record['root']}; "
                       f"bridge P{record['bridge_index']}: {record['bridge']}")
            fig.text(left,.096,role_text,ha="left",va="top",fontsize=6.0,color=INK)
            calibration=record["canonical_mass_calibration"]
            fig.text(left,.038,
                     f"{calibration['selected_head_count']}-head mass calibration: "
                     f"{calibration['native']['answer']} → {calibration['calibrated']['answer']}",
                     ha="left",va="bottom",fontsize=6.0,color=INK)
        save_figure(fig,"data_main_structure_function")


def make_composition_address() -> None:
    """Join the two existing diagnostic views without changing their populations."""
    files=("analysis/figure_data/data_main_composition.csv",
           "analysis/figure_data/data_fig3_diagnosis_address_readout.csv")
    loaded=[]
    for filename in files:
        INPUT_PATHS.add(filename)
        with (ROOT/filename).open(newline="",encoding="utf-8") as handle:
            loaded.append([{**row,"derived_input":filename} for row in csv.DictReader(handle)])
    composition,readouts=loaded
    for row in composition:
        for field in ("total_test_sources","both_constituents_correct","composition_failures","composition_successes"):
            row[field]=int(row[field])
        row["conditional_failure_percent"]=float(row["conditional_failure_percent"])
        if row["composition_successes"]+row["composition_failures"]!=row["both_constituents_correct"]:
            raise ValueError(f"Composition outcomes do not partition the conditional population: {row}")
    for row in readouts:
        row["n"]=int(row["n"]);row["correct"]=int(row["correct"])
        row["accuracy_percent"]=float(row["accuracy_percent"])
        population=unique_record(composition,model=row["model"])
        if (row["n"]!=population["composition_failures"] or
                not np.isclose(row["accuracy_percent"],100*row["correct"]/row["n"])):
            raise ValueError(f"Address readout does not use the displayed composition failures: {row}")
    export_csv("data_main_composition_address_composition",composition)
    export_csv("data_main_composition_address_readout",readouts)
    render_composition_address(composition,readouts)


def render_composition_address(composition,readouts) -> None:
    with plt.rc_context(V3_STYLE):
        fig=plt.figure(figsize=(WIDE,1.90))
        fig.text(.020,.985,"(a) Correct hops, failed composition",ha="left",va="top",
                 fontsize=7.0,fontweight="bold")
        fig.text(.520,.985,"(b) Bridge addresses in those failures",ha="left",va="top",
                 fontsize=7.0,fontweight="bold")
        left=fig.add_axes([.145,.270,.320,.430])
        clean_axis(left,"x")
        y=np.arange(len(MODELS))[::-1]
        rows=[unique_record(composition,model=m) for m in MODELS]
        success=np.array([100*r["composition_successes"]/r["both_constituents_correct"] for r in rows])
        failure=np.array([r["conditional_failure_percent"] for r in rows])
        left.barh(y,success,height=.60,color=BLUE,edgecolor="white",linewidth=.7,
                  label="Composed correct",zorder=3)
        left.barh(y,failure,left=success,height=.60,color=ORANGE,edgecolor="white",
                  linewidth=.7,label="Composed incorrect",zorder=3)
        for yi,row,ok,bad in zip(y,rows,success,failure):
            left.text(ok/2,yi,f"{row['composition_successes']} ({ok:.1f}%)",
                      ha="center",va="center",fontsize=6.0,color="white",fontweight="bold")
            left.text(ok+bad/2,yi,f"{row['composition_failures']} ({bad:.1f}%)",
                      ha="center",va="center",fontsize=6.0,color=INK,fontweight="bold")
        left.set(yticks=y,yticklabels=[f"{MODEL_NAMES[m]}\n$n={r['both_constituents_correct']}$"
                                      for m,r in zip(MODELS,rows)],
                 xlim=(0,100),ylim=(-.55,len(MODELS)-.45),xticks=[0,50,100],
                 xlabel="Share of constituent-correct sources (%)")
        left.spines[["top","right","left"]].set_visible(False)
        left.tick_params(axis="y",length=0,pad=4,labelsize=6.0)
        left.tick_params(axis="x",labelsize=6.0)
        left.xaxis.label.set_size(6.0)
        handles,labels=left.get_legend_handles_labels()
        fig.legend(handles,labels,loc="upper center",bbox_to_anchor=(.290,.855),
                   ncol=2,frameon=False,fontsize=6.0,handlelength=1.3,
                   handletextpad=.40,columnspacing=.9)

        right=fig.add_axes([.590,.270,.385,.430])
        clean_axis(right)
        x=np.arange(len(MODELS));width=.23
        for j,(feature,label,color) in enumerate((("metadata","Metadata",LIGHT_GRAY),
                                                ("attention","Attention",BLUE),
                                                ("full","Full",ORANGE))):
            values=[unique_record(readouts,model=m,feature_set=feature)["accuracy_percent"] for m in MODELS]
            positions=x+(j-1)*width
            right.bar(positions,values,width,color=color,edgecolor=INK,linewidth=.4,
                      zorder=3,label=label)
            if feature=="full":
                for position,value in zip(positions,values):
                    right.text(position,value+2.0,f"{value:.1f}",ha="center",va="bottom",fontsize=6.0)
        right.set(xticks=x,xticklabels=[f"{SHORT[m]}\n$n={unique_record(readouts,model=m,feature_set='full')['n']}$"
                                       for m in MODELS],
                  ylim=(0,112),yticks=[0,50,100],ylabel="Bridge-address accuracy (%)")
        right.tick_params(labelsize=6.0)
        right.yaxis.label.set_size(6.1)
        handles,labels=right.get_legend_handles_labels()
        fig.legend(handles,labels,loc="upper center",bbox_to_anchor=(.780,.855),
                   ncol=3,frameon=False,fontsize=6.0,handlelength=1.3,
                   handletextpad=.4,columnspacing=.9)
        save_figure(fig,"data_main_composition_address")


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only",nargs="*",choices=["composition","diagnosis","causal","content","localization","necessity","ablation","capabilities","ambiguity","case","mechanism_cases","mechanism_causality","joint_rescue","address_routing","mechanism_structure","composition_address"])
    args=parser.parse_args();config=read_json("configs/experiments.json");seeds=config["seeds"]
    tasks={"composition":lambda:make_composition(seeds),"diagnosis":lambda:make_diagnosis(seeds),"causal":make_causal,"content":lambda:make_content(seeds),"localization":make_localization,"necessity":make_necessity,"ablation":lambda:make_ablation(seeds),"capabilities":lambda:make_capabilities(seeds),"ambiguity":make_ambiguity,"case":make_case,"mechanism_cases":make_mechanism_cases,"mechanism_causality":make_mechanism_causality,"joint_rescue":make_joint_rescue,"address_routing":make_address_routing,"mechanism_structure":make_mechanism_structure,"composition_address":make_composition_address}
    requested=list(args.only or tasks)
    # Combined head-profile/knockout panel requires both original collectors.
    if any(name in requested for name in ("localization","necessity")):
        requested=list(dict.fromkeys(requested+["localization","necessity"]))
    collected={name:tasks[name]() for name in requested}
    if "localization" in collected and "necessity" in collected:
        render_head_pair(collected["localization"],*collected["necessity"])
    manifest_name="input_manifest" if not args.only else "input_manifest_"+"_".join(args.only)
    export_csv(manifest_name,[{"path":p,"bytes":(ROOT/p).stat().st_size,"sha256":hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in sorted(INPUT_PATHS)])
    print(f"Read {len(INPUT_PATHS)} input files; see analysis/figure_data/{manifest_name}.csv")

if __name__=="__main__":main()
