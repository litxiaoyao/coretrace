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

def export_csv(name: str, rows: list[dict[str, Any]], *, lineterminator: str = "\r\n") -> None:
    if not rows:
        raise ValueError(f"Empty figure-data table: {name}")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    FIGURE_DATA.mkdir(parents=True, exist_ok=True)
    with (FIGURE_DATA / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator=lineterminator)
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

REF_ORANGE = "#FF7410"  # Figure 7: targeted intervention
REF_GRAY = "#65686A"    # Figure 7: matched random control
REF_BLUE = "#1F77B4"    # Layer-wise analysis: semantic blue
REF_MODELS = ("#4682B4", "#229453", "#CD5C5C")  # A2: blue, green, and red sampled from reference Fig. 4
REF_LIGHT = "#C5C8CA"
PAPER_STYLE = {"font.size": 7.0, "axes.labelsize": 7.0,
               "axes.titlesize": 7.4, "xtick.labelsize": 6.5,
               "ytick.labelsize": 6.5, "legend.fontsize": 6.6,
               "axes.titleweight": "normal", "axes.linewidth": .6,
               "lines.linewidth": 1.15}


def knockout_panels(rows, queries, *, delta, name):
    """Use treatment colors from the supplied reference; model identity uses shape/dash."""
    styles = ("-", (0,(5,2)), (0,(1,1.6)))
    markers = ("o", "s", "^")
    with plt.rc_context(PAPER_STYLE):
        fig, axs = plt.subplots(1, len(queries), figsize=(WIDE,2.22), squeeze=False)
        axes=axs[0]
        fig.subplots_adjust(left=.085,right=.983,bottom=.25,top=.83,
                            wspace=.34 if len(queries)==3 else .22)
        for i,(ax,(query,title)) in enumerate(zip(axes,queries)):
            ax.set_axisbelow(True)
            ax.grid(axis="y",color="#C7C7C7",linestyle=":",lw=.5)
            ax.tick_params(length=2.3,width=.6,pad=2.4)
            if delta: ax.axhline(0,color=REF_GRAY,lw=.65,ls=":",zorder=1)
            all_x=[]; all_y=[]
            # All curves retain the actual measured dose positions. No jitter.
            for selection,color in (("random",REF_GRAY),("selected",REF_ORANGE)):
                for j in (0,2,1):
                    model=MODELS[j]
                    baseline=unique_record(rows,model=model,query=query,selection="native")["accuracy_percent"]
                    measured=sorted((r for r in rows if r["model"]==model and r["query"]==query and r["selection"]==selection),key=lambda r:r["knocked_out"])
                    x=[0]+[r["knocked_out"] for r in measured]
                    y=np.array([baseline]+[r["accuracy_percent"] for r in measured]); y=y-baseline if delta else y
                    all_x.extend(x); all_y.extend(y)
                    ax.plot(x,y,color=color,marker=markers[j],linestyle=styles[j],
                            lw=1.0 if selection=="selected" else .85,
                            markersize=3.7 if j!=1 else 4.1,
                            markerfacecolor=color if j!=1 else "white",
                            markeredgecolor=color,markeredgewidth=.7,
                            zorder=4 if selection=="selected" else 3)
            ax.set(xticks=sorted(set(all_x)),xlim=(-3,max(all_x)+3),xlabel="Heads removed")
            if delta:
                ax.set_ylim(10*np.floor(min(all_y)/10)-2,max(4,10*np.ceil(max(all_y)/10))+1)
            else:
                ax.set_ylim(-2 if max(all_y)<45 else -3,10*np.ceil((max(all_y)+2)/10))
            if delta:
                ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4,integer=True))
            else:
                tick_step=10 if max(all_y)<45 else 20
                ax.set_yticks(np.arange(0,ax.get_ylim()[1]+.1,tick_step))
            ax.set_ylabel("EM change (pp)" if delta else "Exact match (%)")
            # Subfigure captions below axes, as in the reference paper.
            ax.text(.5,-.34,f"({chr(97+i)}) {title}",transform=ax.transAxes,
                    ha="center",va="top",fontsize=7.4)
        treatment=[Line2D([],[],color=c,marker="o",lw=1,markersize=3.8) for c in (REF_ORANGE,REF_GRAY)]
        model_handles=[Line2D([],[],color=INK,marker=m,ls=ls,lw=.9,markersize=3.8,
                             markerfacecolor="white" if i==1 else INK)
                       for i,(m,ls) in enumerate(zip(markers,styles))]
        fig.legend(treatment+model_handles,["Ranked heads","Layer-matched random"]+[MODEL_NAMES[m] for m in MODELS],
                   loc="upper center",bbox_to_anchor=(.52,.99),ncol=5,frameon=False,
                   fontsize=6.5,handlelength=2.0,columnspacing=1.05,handletextpad=.4)
        save_figure(fig,name)


def grouped_accuracy_panels(aggregates, metrics, methods, *, metric_field, method_field,
                            name, width=WIDE, ylabel="Accuracy (%)", short=False):
    """Shared legend and axes for related benchmark panels; preserve recorded SD."""
    with plt.rc_context(PAPER_STYLE):
        n=len(metrics); fig,axes=plt.subplots(1,n,figsize=(width,1.90 if width==WIDE else 1.78),
                                            sharey=True,squeeze=False)
        axes=axes[0]; fig.subplots_adjust(left=.09 if width==WIDE else .14,right=.985,
                                         bottom=.20,top=.73,wspace=.20 if width==WIDE else .25)
        x=np.arange(len(MODELS)); bw=.72/len(methods)
        for i,(ax,(key,title)) in enumerate(zip(axes,metrics)):
            clean_axis(ax)
            for j,(method,label,color) in enumerate(methods):
                data=[unique_record(aggregates,model=m,**{metric_field:key,method_field:method}) for m in MODELS]
                vals=[r["mean_percent"] for r in data]; err=[r["sample_sd_percent"] for r in data]
                pos=x+(j-(len(methods)-1)/2)*bw
                ax.bar(pos,vals,bw*.92,color=color,label=label,zorder=3)
                ax.errorbar(pos,vals,yerr=err,fmt="none",ecolor=INK,elinewidth=.7,capsize=1.8,zorder=4)
                for xx,v in zip(pos,vals):
                    if v==0: ax.text(xx,1.8,"0",ha="center",va="bottom",fontsize=6.0,color=INK)
            ax.set(xticks=x,
                   xticklabels=["4B","8B","L8B"] if short else ["Qwen3-4B","Qwen3-8B","Llama-8B"],
                   ylim=(0,105),yticks=[0,25,50,75,100])
            ax.set_title(f"({chr(97+i)}) {title}",loc="left",pad=4,fontsize=7.0)
            ax.tick_params(axis="x",labelsize=6.1 if width==WIDE else 6.2)
        axes[0].set_ylabel(ylabel)
        fig.legend(*axes[0].get_legend_handles_labels(),loc="upper center",bbox_to_anchor=(.53,.99),
                   ncol=len(methods),frameon=False,handlelength=1.2,handletextpad=.4,columnspacing=.9)
        save_figure(fig,name)


def render_causal(factors, contrasts, access):
    """One crossed-condition matrix and one aligned forest plot; all original CIs."""
    with plt.rc_context(PAPER_STYLE):
        fig = plt.figure(figsize=(WIDE,2.48))
        matrix = fig.add_axes([.155,.23,.36,.53])
        forest = fig.add_axes([.565,.23,.255,.53],sharey=matrix)
        fig.text(.025,.975,"(a) Composed accuracy (%)",ha="left",va="top",fontsize=7.5,fontweight="bold")
        fig.text(.55,.975,"(b) Pattern effects and interaction",ha="left",va="top",fontsize=7.5,fontweight="bold")
        keys = ("native","conditional_only","mass_only","both")
        contrast_keys = ("conditional_effect_native_mass","conditional_effect_fixed_mass","interaction")
        for i,model in enumerate(MODELS):
            y = 2-i; color = REF_ORANGE
            vals = np.array([unique_record(factors,model=model,method=k)["accuracy_percent"] for k in keys])
            effects = [unique_record(contrasts,model=model,contrast=k) for k in contrast_keys]
            est = np.array([r["estimate_pp"] for r in effects])
            if not np.allclose([vals[1]-vals[0],vals[3]-vals[2],
                                (vals[3]-vals[2])-(vals[1]-vals[0])],est):
                raise ValueError(f"Crossed cells and contrasts disagree for {model}")
            for j,v in enumerate(vals):
                combined = j==3
                matrix.add_patch(Rectangle((j-.455,y-.35),.91,.70,
                    facecolor=matplotlib.colors.to_rgba(color,.12) if combined else "#F6F6F6",
                    edgecolor=color if combined else "#D4D7DA",lw=.8 if combined else .4))
                matrix.text(j,y,f"{v:.0f}",ha="center",va="center",fontsize=8.6,
                            fontweight="bold" if combined else "normal")
            for j,(r,offset,marker) in enumerate(zip(effects,(.25,0,-.25),("o","o","D"))):
                yy = y+offset; v = r["estimate_pp"]
                lo,hi = r["CI95_low_pp"],r["CI95_high_pp"]
                contrast_color=(REF_GRAY,REF_BLUE,REF_ORANGE)[j]
                forest.errorbar(v,yy,xerr=[[v-lo],[hi-v]],fmt=marker,color=contrast_color,
                    markerfacecolor="white" if j==0 else contrast_color,markeredgewidth=.8,
                    markersize=3.6,capsize=1.6,elinewidth=.9,capthick=.7,zorder=4)
                forest.text(1.055,yy,f"{v:+.0f} [{lo:.0f}, {hi:.0f}]",
                    transform=forest.get_yaxis_transform(),ha="left",va="center",fontsize=6.4,
                    fontweight="bold" if j==2 else "normal",color=contrast_color if j==2 else INK)
        matrix.set(xlim=(-.5,3.5),ylim=(-.5,2.5),xticks=range(4),
                   xticklabels=["Receiver","Direct","Receiver","Direct"],
                   yticks=[2,1,0],yticklabels=[MODEL_NAMES[m] for m in MODELS])
        matrix.tick_params(axis="x",top=True,labeltop=True,bottom=False,labelbottom=False,length=0,pad=2)
        matrix.tick_params(axis="y",length=0,pad=4)
        for spine in matrix.spines.values(): spine.set_visible(False)
        for x,label in ((.25,"Native mass"),(.75,"Calibrated mass")):
            matrix.text(x,1.15,label,transform=matrix.transAxes,ha="center",va="bottom",fontsize=6.8)
        matrix.axvline(1.5,color="#D0D4D7",lw=.6)
        clean_axis(forest,"x")
        forest.axvline(0,color=GRAY,lw=.8,zorder=2)
        for y in (.5,1.5): forest.axhline(y,color=GRID,lw=.45,zorder=1)
        forest.set(xlim=(-12,27),xticks=[-10,0,10,20],xlabel="Effect on accuracy (pp)")
        forest.tick_params(axis="y",left=False,labelleft=False)
        forest.spines["left"].set_visible(False)
        forest.text(1.055,1.075,"Estimate [95% CI]",transform=forest.transAxes,
                    ha="left",va="bottom",fontsize=6.2)
        handles = [Line2D([],[],color=c,marker=m,markerfacecolor=f,linestyle="none",markersize=4)
                   for c,m,f in ((REF_GRAY,"o","white"),(REF_BLUE,"o",REF_BLUE),(REF_ORANGE,"D",REF_ORANGE))]
        fig.legend(handles,["Native mass","Calibrated mass","Interaction"],
                   loc="lower right",bbox_to_anchor=(.985,.005),ncol=3,frameon=False,
                   handlelength=1.0,columnspacing=1.0,handletextpad=.3,fontsize=6.3)
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
    """Compare exact intersections on one common membership grid."""
    with plt.rc_context(PAPER_STYLE):
        counts = {m:dict(intersection_rows(sets_by_model[m])) for m in MODELS}
        patterns = sorted(set().union(*(c.keys() for c in counts.values())),
                          key=lambda p:(sum(p),p),reverse=True)
        fig = plt.figure(figsize=(WIDE,2.30))
        gs = fig.add_gridspec(2,1,left=.16,right=.985,top=.78,bottom=.085,
                              height_ratios=[2.1,1],hspace=.06)
        top = fig.add_subplot(gs[0]); bot = fig.add_subplot(gs[1],sharex=top)
        x=np.arange(len(patterns)); width=.24
        max_n=max(v for c in counts.values() for v in c.values())
        clean_axis(top)
        for i,(m,c) in enumerate(zip(MODELS,REF_MODELS)):
            n=[counts[m].get(p,0) for p in patterns]; pos=x+(i-1)*width
            top.bar(pos,n,width=width*.9,color=c,edgecolor="none",zorder=3,
                    label=f"{MODEL_NAMES[m]} ($k={len(sets_by_model[m][0])}$)")
            for xx,v in zip(pos,n):
                top.text(xx,v+.5,str(v),ha="center",va="bottom",fontsize=6.5,
                         color=c if v else GRAY)
        top.set(xlim=(-.55,len(patterns)-.45),ylim=(0,max_n*1.23),ylabel="Heads")
        top.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4,integer=True))
        top.tick_params(axis="x",bottom=False,labelbottom=False)
        top.spines["bottom"].set_visible(False)
        bot.axhspan(-.5,.5,color="#FFF0E4",zorder=0)
        bot.axhspan(1.5,2.5,color="#F4F4F4",zorder=0)
        for i,p in enumerate(patterns):
            active=[j for j,v in enumerate(p) if v]
            bot.scatter([i]*3,range(3),s=12,color="#D4D7DA",zorder=1,edgecolors="none")
            if len(active)>1: bot.plot([i,i],[min(active),max(active)],color=INK,lw=.9,zorder=2)
            bot.scatter([i]*len(active),active,s=18,
                        color=[REF_ORANGE if j==0 else INK for j in active],
                        zorder=3,edgecolors="none")
        bot.set(yticks=[0,1,2],yticklabels=["Ranked","Direct","Composed"],ylim=(2.5,-.5),xticks=[])
        bot.tick_params(axis="y",length=0,pad=3)
        bot.get_yticklabels()[0].set_color(REF_ORANGE)
        bot.get_yticklabels()[0].set_fontweight("medium")
        for spine in bot.spines.values(): spine.set_visible(False)
        fig.legend(*top.get_legend_handles_labels(),loc="upper center",bbox_to_anchor=(.53,.98),
                   ncol=3,frameon=False,handlelength=1.3,columnspacing=1.5)
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


def render_necessity(raw, measured_sizes):
    # Verify that the compact panels still contain every measured dose.
    for model in MODELS:
        for query in ("composed","direct_first","direct_target"):
            for selection in ("selected","random"):
                actual = sorted(r["knocked_out"] for r in raw if r["model"]==model
                                and r["query"]==query and r["selection"]==selection)
                if actual != sorted(measured_sizes[model]):
                    raise ValueError(f"Incomplete knockout series: {model}/{query}/{selection}")
    knockout_panels(raw, (("composed","Composed"),("direct_first","First hop"),
                          ("direct_target","Second hop")),
                    delta=True,name="data_app_necessity")


def render_content(aggregated):
    grouped_accuracy_panels(aggregated,(("edited_new_follow","Edited value"),("original_correct_then_new","Joint EM")),
                            (("native","Native",REF_GRAY),("final","CoReTrace",REF_ORANGE)),metric_field="metric",
                            method_field="method",name="data_fig5_content",width=COL,ylabel="Queries (%)",short=True)


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
    grouped_accuracy_panels(aggregates,metrics,((False,"Adaptation",REF_GRAY),(True,"+ Restoration",REF_ORANGE)),
                            metric_field="query",method_field="projection_restoration",name="data_app_ablation")


def render_capabilities(aggregates):
    grouped_accuracy_panels(aggregates,(("hotpot","HotpotQA"),("mmlu","MMLU"),("gsm8k","GSM8K")),
                            (("native","Native",REF_GRAY),("fullft","Full fine-tuning",REF_LIGHT),("final","CoReTrace",REF_ORANGE)),
                            metric_field="dataset",method_field="method",name="data_app_capabilities")

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
    knockout_panels(rows, (("composed","Composed"),("direct_target","Direct second hop")),
                    delta=False,name="data_main_head_causality")


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
    with plt.rc_context(PAPER_STYLE):
        fig,ax = plt.subplots(figsize=(COL,1.68))
        fig.subplots_adjust(left=.32,right=.94,bottom=.25,top=.77)
        clean_axis(ax,"x")
        ys = np.arange(len(MODELS))[::-1]
        largest = max(r["both_repairs"] for r in rows)
        labels = []
        for i,(y,model) in enumerate(zip(ys,MODELS)):
            joint = unique_record(rows,model=model,group="both_required")
            other = unique_record(rows,model=model,group="at_least_one_single_succeeds")
            if joint["count"]+other["count"] != joint["both_repairs"]:
                raise ValueError(f"Inconsistent rescue count: {model}")
            labels.append(f"{MODEL_NAMES[model]}\n($n={joint['native_failures']}$)")
            for j,(count,left,color) in enumerate(((joint["count"],0,REF_ORANGE),
                                                   (other["count"],joint["count"],REF_LIGHT))):
                ax.barh(y,count,left=left,height=.60,color=color,edgecolor="white",lw=.6,zorder=3,
                        label=("Joint-only","Single arm also correct")[j] if i==0 else None)
                if count:
                    ax.text(left+count/2,y,str(count),ha="center",va="center",fontsize=7.0,
                            fontweight="bold",color=INK)
            ax.text(joint["both_repairs"]+.55,y,str(joint["both_repairs"]),ha="left",va="center",fontsize=6.8)
        ax.set(yticks=ys,yticklabels=labels,ylim=(-.6,len(MODELS)-.4),
               xlim=(0,largest+3.6),xticks=list(range(0,int(largest)+2,10)),
               xlabel="Native failures repaired (count)")
        ax.spines[["top","right","left"]].set_visible(False)
        ax.tick_params(axis="y",length=0,pad=3,labelsize=6.4)
        handles,labels = ax.get_legend_handles_labels()
        fig.legend(handles,labels,loc="upper center",bbox_to_anchor=(.52,.99),
                   ncol=2,frameon=False,fontsize=6.4,handlelength=1.2,
                   handletextpad=.4,columnspacing=.9)
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
    """Preserve exact intersections, model comparisons and both full head portraits."""
    with plt.rc_context(PAPER_STYLE):
        fig=plt.figure(figsize=(WIDE,3.30))
        fig.text(.025,.982,"(a) Head-set intersections",ha="left",va="top",fontsize=7.5,fontweight="bold")
        model=MODELS[0]; k=data["models"][model]["k"]
        fig.text(.025,.923,f"{MODEL_NAMES[model]} ($k={k}$)",ha="left",va="top",fontsize=6.7)
        intersections=sorted([r for r in overlaps if r["model"]==model and r["count"]>0],
                             key=lambda r:(-r["count"],-r["selected"],-r["direct"],-r["composed"]))
        counts=[r["count"] for r in intersections]; x=np.arange(len(counts))
        top=fig.add_axes([.145,.735,.235,.145]); clean_axis(top)
        top.bar(x,counts,width=.65,color=INK,zorder=3)
        for xx,v in zip(x,counts): top.text(xx,v+.45,str(v),ha="center",va="bottom",fontsize=6.6)
        top.set(xlim=(-.55,len(counts)-.45),ylim=(0,max(counts)+5),yticks=[0,10,20],ylabel="Heads")
        top.tick_params(axis="x",bottom=False,labelbottom=False)
        top.spines["bottom"].set_visible(False)
        membership=fig.add_axes([.145,.592,.235,.112])
        membership.set(xlim=top.get_xlim(),ylim=(2.5,-.5),xticks=[],yticks=[0,1,2],
                       yticklabels=["Selected","Direct top-k","Composed top-k"])
        for y in (0,2): membership.axhspan(y-.5,y+.5,color="#F2F3F4",zorder=0)
        for j,row in enumerate(intersections):
            active=[y for y,key in enumerate(("selected","direct","composed")) if row[key]]
            membership.scatter([j]*3,range(3),s=12,color="#D4D7DA",zorder=1,edgecolors="none")
            if len(active)>1: membership.plot([j,j],[min(active),max(active)],color=INK,lw=.85,zorder=2)
            membership.scatter([j]*len(active),active,s=17,color=INK,zorder=3,edgecolors="none")
        membership.tick_params(length=0,pad=3,labelsize=6.3)
        for spine in membership.spines.values(): spine.set_visible(False)
        fig.text(.418,.982,"(b) Root-to-bridge preference",ha="left",va="top",fontsize=7.5,fontweight="bold")
        ax=fig.add_axes([.543,.641,.427,.205]); clean_axis(ax,"x")
        vals=[]
        for i,model in enumerate(MODELS):
            y=2-i
            for group,offset,color,style in (("selected",.13,REF_ORANGE,"-"),
                                             ("random_layer_matched",-.13,REF_GRAY,"-")):
                points=[unique_record(profiles,model=model,head_set=group,query=q)["bridge_minus_root_pp"]
                        for q in ("composed","direct_target")]; vals.extend(points)
                ax.plot(points,[y+offset]*2,linestyle=style,color=color,lw=1.2,zorder=3)
                ax.plot(points[0],y+offset,"o",markersize=4,markerfacecolor="white",markeredgecolor=color,markeredgewidth=.9,zorder=4)
                ax.plot(points[1],y+offset,"o",markersize=4,markerfacecolor=color,markeredgecolor=color,zorder=4)
        ax.axvline(0,color=GRAY,lw=.7,zorder=2)
        lo=5*np.floor((min(vals)-3)/5); hi=5*np.ceil((max(vals)+3)/5)
        ax.set(yticks=[2,1,0],yticklabels=[MODEL_NAMES[m] for m in MODELS],ylim=(-.5,2.5),
               xlim=(lo,hi),xticks=np.arange(np.ceil(lo/10)*10,hi+1,10),xlabel="Bridge - root mass (pp)")
        ax.tick_params(axis="y",length=0,pad=3); ax.spines["left"].set_visible(False)
        handles=[Line2D([],[],marker="o",linestyle="none",color=INK,markerfacecolor="white",markersize=4),
                 Line2D([],[],marker="o",linestyle="none",color=INK,markersize=4),
                 Line2D([],[],color=REF_ORANGE,lw=1.05),Line2D([],[],color=REF_GRAY,lw=.9)]
        fig.legend(handles,["Composed","Direct","Selected","Matched random"],loc="upper center",
                   bbox_to_anchor=(.706,.925),ncol=4,frameon=False,fontsize=6.3,
                   handlelength=1.2,handletextpad=.3,columnspacing=.7)
        matrices=[100*np.array([e["head"]["paragraph_mass"][q]["all_question_mean"]
                                for q in ("composed","direct_target")]) for e in examples]
        maximum=10*np.ceil(max(float(m.max()) for m in matrices)/10)
        norm=matplotlib.colors.Normalize(vmin=0,vmax=maximum)
        for i,(example,matrix,left) in enumerate(zip(examples,matrices,(.025,.525))):
            model=example["model"]; record=example["record"]; head=example["head"]
            fig.text(left,.505,f"({chr(99+i)}) {MODEL_NAMES[model]} | L{head['layer']}H{head['head']}",
                     ha="left",va="top",fontsize=7.3,fontweight="bold")
            questions=[textwrap.fill(prefix+": "+record["questions"][query]["question"],
                        width=67,subsequent_indent="    ",break_long_words=False,break_on_hyphens=False)
                        for prefix,query in (("q12","composed"),("q2","direct_target"))]
            fig.text(left,.457,"\n".join(questions),ha="left",va="top",fontsize=6.4,linespacing=1.10)
            hm=fig.add_axes([left+.046,.250,.423,.105])
            im=hm.imshow(matrix,cmap="Blues",norm=norm,aspect="auto",interpolation="nearest")
            for row in range(matrix.shape[0]):
                for col in range(matrix.shape[1]):
                    v=matrix[row,col]
                    hm.text(col,row,f"{v:.1f}",ha="center",va="center",fontsize=6.3,
                            color="white" if v>maximum*.55 else INK)
            for key,color in (("root_index",REF_ORANGE),("bridge_index",REF_BLUE)):
                hm.add_patch(Rectangle((record[key]-.5,-.5),1,2,fill=False,edgecolor=color,lw=1.2))
            hm.set(xticks=np.arange(matrix.shape[1]),xticklabels=[f"P{j}" for j in range(matrix.shape[1])],
                   yticks=[0,1],yticklabels=["q12","q2"])
            hm.tick_params(axis="both",length=0,pad=2,labelsize=6.2)
            for spine in hm.spines.values(): spine.set_visible(False)
            fig.text(left,.173,f"Root P{record['root_index']}: {record['root']}; bridge P{record['bridge_index']}: {record['bridge']}",
                     ha="left",va="top",fontsize=6.3)
            cal=record["canonical_mass_calibration"]
            fig.text(left,.126,f"{cal['selected_head_count']}-head mass calibration: {cal['native']['answer']} $\\to$ {cal['calibrated']['answer']}",
                     ha="left",va="top",fontsize=6.3)
        cb=fig.colorbar(im,cax=fig.add_axes([.43,.032,.29,.018]),orientation="horizontal",ticks=[0,maximum/2,maximum])
        cb.ax.xaxis.set_ticks_position("top"); cb.ax.tick_params(length=1.8,pad=1,labelsize=6.1)
        cb.outline.set_visible(False)
        fig.text(.412,.041,"Attention mass (%)",ha="right",va="center",fontsize=6.4)
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


# BEGIN STORY_REVISION_V5: derived views and mechanism figures
def _revision_read_rows(name):
    filename = "analysis/figure_data/" + name
    INPUT_PATHS.add(filename)
    with (ROOT / filename).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))

def make_interaction_revision():
    rows=_revision_read_rows('data_fig4_causal_factorial.csv')
    contrasts=_revision_read_rows('data_fig4_causal_factorial_contrasts.csv')
    lookup={(r['model'],r['method']):float(r['accuracy_percent']) for r in rows}
    ci={r['model']:[float(r[k]) for k in ('estimate_pp','CI95_low_pp','CI95_high_pp')] for r in contrasts if r['contrast']=='interaction'}
    fig,axs=plt.subplots(1,3,figsize=(6.75,2.13),sharey=True)
    fig.subplots_adjust(left=.075,right=.985,top=.77,bottom=.24,wspace=.15)
    for ax,model in zip(axs,MODELS):
        native=[lookup[(model,k)] for k in ('native','conditional_only')]
        calib=[lookup[(model,k)] for k in ('mass_only','both')]
        ax.plot([0,1],native,'o-',color=GRAY,label='Native access',lw=1.6,ms=4)
        ax.plot([0,1],calib,'o-',color=ORANGE,label='Calibrated access',lw=1.9,ms=4)
        for i,y in enumerate(native): ax.annotate(f'{y:.0f}',(i,y),xytext=(0,-10),textcoords='offset points',ha='center',color='#555555',fontsize=7)
        for i,y in enumerate(calib): ax.annotate(f'{y:.0f}',(i,y),xytext=(0,4),textcoords='offset points',ha='center',color='#9B542F',fontsize=7,fontweight='bold')
        est,lo,hi=ci[model]
        ax.set_title(MODEL_NAMES[model],fontweight='bold',pad=5)
        ax.set_xticks([0,1],['Receiver','Direct query']); ax.set_xlim(-.20,1.20); ax.set_ylim(16,86)
        ax.set_yticks([20,40,60,80]); ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',color=GRID,lw=.5,ls='--');ax.set_axisbelow(True)
        ax.text(.5,-.31,f'Interaction: +{est:.0f} pp [{lo:.0f}, {hi:.0f}]',ha='center',va='top',transform=ax.transAxes,fontsize=7,fontweight='bold')
    axs[0].set_ylabel('Composed EM (%)')
    h,l=axs[0].get_legend_handles_labels();fig.legend(h,l,loc='upper center',bbox_to_anchor=(.5,1.015),ncol=2,frameon=False,fontsize=7.2)
    save_figure(fig,'data_main_interaction_revision')


def _story_canvas(w, h):
    fig = plt.figure(figsize=(w,h), facecolor='white')
    ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis('off')
    return fig, ax


def _story_box(ax, x,y,w,h, title, detail='', color='#5E80B8', fill='#F0F4FA', fs=7.1, lw=.8):
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((x,y),w,h, boxstyle='round,pad=0.15,rounding_size=1.1', facecolor=fill, edgecolor=color, lw=lw))
    ax.text(x+w/2,y+h*(.64 if detail else .5),title,ha='center',va='center',fontsize=fs,fontweight='bold',color=INK,linespacing=1.15)
    if detail: ax.text(x+w/2,y+h*.28,detail,ha='center',va='center',fontsize=fs-.7,color=INK,linespacing=1.2)


def _story_arrow(ax, x1,y1,x2,y2, color='#92979E', label=None, lw=1.1, style='-'):
    ax.annotate('',(x2,y2),(x1,y1),arrowprops=dict(arrowstyle='-|>',color=color,lw=lw,linestyle=style,shrinkA=1,shrinkB=1,mutation_scale=7))
    if label: ax.text((x1+x2)/2,(y1+y2)/2+2,label,ha='center',va='bottom',fontsize=6.1,color=INK)


def _story_heading(ax, x,y,t, fs=8):
    ax.text(x,y,t,ha='left',va='top',fontsize=fs,fontweight='bold',color=INK)


def _story_cases():
    return read_json('analysis/figure_data/data_revision_case_records.json')


def make_story_teaser():
    d=_story_cases()['corvinus']; fig, ax=_story_canvas(3.25,3.10)
    root,bridge,gold=d['chain']
    _story_heading(ax,2,99,'(a) Correct hops, failed composition')
    ax.text(50,93,'Same ten-paragraph context',ha='center',va='center',fontsize=6.5,color=INK)
    _story_box(ax,2,75,28,12,'P0: '+root,'Root',color=ORANGE,fill='#FCF0E6',fs=6.4)
    _story_box(ax,34,75,35,12,'P1: '+bridge,'Bridge',color=BLUE,fs=6.1)
    _story_box(ax,74,75,24,12,gold,'Answer',color='#4D8A71',fill='#EDF6F1',fs=6.4)
    _story_arrow(ax,30,81,34,81); _story_arrow(ax,69,81,74,81)
    ax.text(32,88,'father',ha='center',fontsize=5.5);ax.text(71.5,88,'father',ha='center',fontsize=5.5)
    ax.text(50,70,'Both constituent answers correct in all three models',ha='center',fontsize=6.4,color='#35745B')
    _story_box(ax,4,55,92,12,'Who is John Corvinus\'s paternal grandfather?', 'Native: '+d['native_composed']+'  (incorrect)',color='#B86A67',fill='#FBEFEE',fs=7)
    ax.plot([2,98],[50.5,50.5],color='#D3D7DC',lw=.6)
    _story_heading(ax,2,47,'(b) Evidence use, not just evidence location')
    _story_box(ax,2,28,29,12,'Locate','Bridge address',color=BLUE,fs=7)
    _story_box(ax,36,28,28,12,'Route','Access mass',color=ORANGE,fill='#FCF0E6',fs=7)
    _story_box(ax,69,28,29,12,'Read','Local weights',color='#4D8A71',fill='#EDF6F1',fs=7)
    _story_arrow(ax,31,34,36,34); _story_arrow(ax,64,34,69,34)
    ax.text(50,23,'Routing and reading interact in evidence use',ha='center',fontsize=6.6,fontweight='bold')
    _story_arrow(ax,50,20,50,15,color='#4D8A71')
    _story_box(ax,4,2,92,12,'CoReTrace: '+d['final_composed']+'  (correct)','Recorded in all three models',color='#4D8A71',fill='#EDF6F1',fs=7.5)
    save_figure(fig,'figure1_teaser_revision')


def make_story_diagnosis():
    fig,ax=_story_canvas(6.75,1.87)
    _story_heading(ax,1,99,'(a) Locate evidence-access heads',fs=7.3)
    _story_heading(ax,34,99,'(b) Factorize bridge attention',fs=7.3)
    _story_heading(ax,69,99,'(c) Cross interventions',fs=7.3)
    for x in (32,67):ax.plot([x,x],[3,96],color='#D3D7DC',lw=.7)
    _story_box(ax,2,67,28,17,'Same context','Root + bridge + distractors',color=BLUE,fs=7)
    _story_arrow(ax,16,67,8,58); _story_arrow(ax,16,67,24,58)
    _story_box(ax,2,43,13,15,'Composed',r'$q_{12}$',color=ORANGE,fill='#FCF0E6',fs=6.7)
    _story_box(ax,17,43,13,15,'Direct hop',r'$q_2$',color=BLUE,fs=6.7)
    _story_arrow(ax,8.5,43,16,32);_story_arrow(ax,23.5,43,16,32)
    _story_box(ax,4,15,24,17,'Rank heads',r'$\Delta$ bridge mass',color=BLUE,fs=7)
    ax.text(16,6.5,'Knockout  |  Address readout',ha='center',va='center',fontsize=6.8)
    # Illustrative paragraph-level allocation, not measurements.
    for i,(lab,col) in enumerate((('Root',ORANGE),('Bridge',BLUE),('Other','#D4D8DD'))):
        x=35+i*10.5
        _story_box(ax,x,70,9.5,13,lab,color=col,fill='#F7F8FA',fs=6.7)
    _story_arrow(ax,50.3,70,50.3,57,color=BLUE,lw=2.0)
    ax.text(52,64,r'Access mass $m$',fontsize=7,color=BLUE,va='center')
    ax.add_patch(__import__('matplotlib').patches.Rectangle((36.3,22),27.5,33,facecolor='#F0F4FA',edgecolor=BLUE,lw=.8))
    for i,(t,h) in enumerate(zip(('entity','relation','value','other'),(9,18,23,6))):
        x=38.1+i*6.4
        ax.add_patch(__import__('matplotlib').patches.Rectangle((x,30),4.6,h,facecolor='#669780',edgecolor='none',alpha=.85))
        ax.text(x+2.3,25.5,t,ha='center',va='center',fontsize=5.7)
    ax.text(50,16,r'Conditional pattern $\rho$ (schematic)',ha='center',fontsize=6.6,color='#35745B')
    ax.text(50,8.0,r'$c_B=m\sum_{k\in B}\rho_k v_k$',ha="center",fontsize=8,fontweight="bold")
    ax.text(81,81,'Receiver pattern',ha='center',fontsize=6.3); ax.text(93,81,'Direct pattern',ha='center',fontsize=6.3)
    ax.text(69.2,65,'Native\nmass',ha='left',va='center',fontsize=6.2)
    ax.text(69.2,42,'Fixed\nmass',ha='left',va='center',fontsize=6.2)
    for x,y,lab,detail,col,fill in [(76,56,'Native',r'$m,\rho$',GRAY,'#F2F3F4'),(88,56,'Pattern',r'$m,\rho^{dir}$','#4D8A71','#EDF6F1'),(76,33,'Mass',r'$\tau,\rho$',ORANGE,'#FCF0E6'),(88,33,'Both',r'$\tau,\rho^{dir}$',BLUE,'#F0F4FA')]:
        _story_box(ax,x,y,10.5,19,lab,detail,color=col,fill=fill,fs=7)
    ax.text(84,22,'Receiver V and O unchanged',ha='center',fontsize=6.2)
    ax.text(84,8,'Interaction + joint-only rescue',ha='center',fontsize=6.4,fontweight='bold')
    save_figure(fig,'figure2_diagnosis_revision')


def make_story_repair():
    fig,ax=_story_canvas(6.75,1.70)
    _story_heading(ax,1,99,'(a) Offline: improve the localized evidence-access heads')
    _story_box(ax,2,63,18,21,'Selected heads','Frozen head identities',color=BLUE,fs=7)
    _story_box(ax,26,63,18,21,'Adapt Q/K/V/O','Answer-only training',color=ORANGE,fill='#FCF0E6',fs=7)
    _story_box(ax,50,63,20,21,'Restore native V/O','Fixed prefill scopes',color='#92979E',fill='#F5F6F7',fs=7)
    _story_box(ax,76,63,22,21,'Fit address readout','Adapted/restored features',color=BLUE,fs=7)
    for x1,x2 in [(20,26),(44,50),(70,76)]: _story_arrow(ax,x1,73.5,x2,73.5)
    ax.plot([1,99],[55,55],color='#D3D7DC',lw=.7)
    _story_heading(ax,1,51,'(b) Inference: use the address signal to select original evidence')
    _story_box(ax,2,12,16,23,'Question + context','Original paragraphs',color=GRAY,fill='#F6F7F8',fs=6.9)
    _story_arrow(ax,18,23.5,23,23.5)
    _story_box(ax,23,12,18,23,'Title graph','Root + candidates',color=BLUE,fs=7)
    _story_arrow(ax,41,23.5,46,32);_story_arrow(ax,41,23.5,46,12)
    _story_box(ax,46,24,22,16,'Unique: direct choice',color=BLUE,fs=6.6)
    _story_box(ax,46,4,22,16,'Multiple: rank by reader',color=BLUE,fs=6.5)
    _story_arrow(ax,68,32,73,24);_story_arrow(ax,68,12,73,23)
    _story_box(ax,73,12,25,23,'Adapted model','Root + bridge $\\to$ answer',color='#4D8A71',fill='#EDF6F1',fs=7)
    ax.text(32,4.2,'No usable graph: retain full context',ha='center',fontsize=6.0,color=INK)
    save_figure(fig,'figure3_method_revision')


def make_joint_case_revision():
    case=_story_cases()['angela']; rows=_revision_read_rows('data_revision_joint_counts.csv')
    fig,ax=_story_canvas(3.25,2.47)
    _story_heading(ax,1,99,'(a) A joint-only repair in Llama-3.1-8B',fs=7.4)
    ax.text(2,88,'Q: Who is the mother of the director of Angela?',ha='left',fontsize=6.6)
    _story_box(ax,2,72,34,12,'P7: Angela','directed by Rebecca Miller',color=ORANGE,fill='#FCF0E6',fs=6.4)
    _story_arrow(ax,36,78,41,78,color=BLUE)
    _story_box(ax,41,72,57,12,'P5: Rebecca Miller','daughter of Arthur Miller and Inge Morath',color=BLUE,fs=6.1)
    for i,r in enumerate(case['arms']):
        x=2+(i%2)*49;y=53-(i//2)*15
        name={'native':'Native','mass_only':'Mass only','conditional_only':'Pattern only','both':'Both'}[r['method']]
        color='#4D8A71' if r['correct'] else '#B86A67';fill='#EDF6F1' if r['correct'] else '#FBEFEE'
        _story_box(ax,x,y,47,12,name,r['answer']+('  (correct)' if r['correct'] else ''),color=color,fill=fill,fs=6.6)
    _story_heading(ax,1,33,'(b) Joint-only corrections across models',fs=7.4)
    bar=fig.add_axes([.23,.098,.73,.163]);bar.spines[['top','right','left','bottom']].set_visible(False)
    vals={r['model']:r for r in rows}; y=np.arange(3)[::-1]; joint=np.array([int(vals[m]['joint_only']) for m in MODELS]); total=np.array([int(vals[m]['both_repairs']) for m in MODELS]);
    bar.barh(y,joint,height=.57,color=ORANGE,label='Joint only');bar.barh(y,total-joint,left=joint,height=.57,color='#D4D8DD',label='Single arm also correct')
    for yi,j,t in zip(y,joint,total):bar.text(j/2,yi,str(j),ha='center',va='center',fontsize=6.4,fontweight='bold');bar.text(t+.6,yi,str(t),ha='left',va='center',fontsize=6.2)
    bar.set(yticks=y,yticklabels=['Qwen 4B','Qwen 8B','Llama 8B'],xlim=(0,33),xticks=[]);bar.tick_params(axis='both',labelsize=6,length=0,pad=2);bar.grid(axis='x',color='#E4E6E8',ls='--',lw=.5);bar.set_axisbelow(True)
    fig.legend(*bar.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.53,.006),ncol=2,frameon=False,fontsize=5.9,handlelength=1.2,columnspacing=.8)
    save_figure(fig,'data_main_joint_case_revision')


def make_content_case_revision():
    case=_story_cases()['angela'];r=case['reciprocal_exchange'];rows=_revision_read_rows('data_revision_content.csv')
    fig,ax=_story_canvas(3.25,2.47)
    _story_heading(ax,1,99,'(a) Same question, same selected address',fs=7.4)
    _story_box(ax,2,66,46,19,'Original | P5','mother: '+r['original_value'],color=BLUE,fs=7)
    _story_box(ax,52,66,46,19,'Edited | P5','mother: '+r['edited_value'],color=BLUE,fs=7)
    ax.text(50,90,'Reciprocal swap with P9 (Oskar Roehler)',ha='center',fontsize=6.4)
    _story_arrow(ax,25,66,25,55,color='#4D8A71');_story_arrow(ax,75,66,75,55,color='#4D8A71')
    _story_box(ax,2,43,46,12,r['original_answer'],color='#4D8A71',fill='#EDF6F1',fs=7)
    _story_box(ax,52,43,46,12,r['edited_answer'],color='#4D8A71',fill='#EDF6F1',fs=7)
    ax.text(50,38,'Complete CoReTrace follows both local values',ha='center',fontsize=6.5,fontweight='bold')
    _story_heading(ax,1,33,'(b) Joint original / edited correctness',fs=7.4)
    bar=fig.add_axes([.23,.103,.73,.158]); bar.spines[['top','right','left','bottom']].set_visible(False)
    vals={r['model']:r for r in rows}; y=np.arange(3)[::-1]; n=[float(vals[m]['native_joint_accuracy']) for m in MODELS];f=[float(vals[m]['final_joint_accuracy']) for m in MODELS]
    for yi,a,b in zip(y,n,f):
        bar.plot([a,b],[yi,yi],color='#B7C6D4',lw=2);bar.scatter([a],[yi],color=GRAY,s=13,zorder=3);bar.scatter([b],[yi],color='#4D8A71',s=17,zorder=3);bar.text(a-3,yi,str(int(a)),ha='right',va='center',fontsize=6);bar.text(b+3,yi,str(int(b)),ha='left',va='center',fontsize=6,fontweight='bold')
    bar.set(yticks=y,yticklabels=['Qwen 4B','Qwen 8B','Llama 8B'],xlim=(0,100),ylim=(-.28,2.28),xticks=[]);bar.tick_params(axis='both',labelsize=6,length=0,pad=2);bar.grid(axis='x',color='#E4E6E8',ls='--',lw=.5);bar.set_axisbelow(True)
    fig.text(.53,.005,'Native (gray)   CoReTrace (green)  |  %',ha='center',va='bottom',fontsize=6)
    save_figure(fig,'data_main_content_case_revision')


def make_repair_chain_revision():
    rows=_revision_read_rows('data_revision_mechanism_repair.csv'); lookup={r['model']:r for r in rows}
    fig,axs=plt.subplots(1,3,figsize=(6.75,1.89),sharey=True)
    fig.subplots_adjust(left=.07,right=.99,top=.70,bottom=.19,wspace=.22)
    x=np.arange(3);width=.29;names=['Qwen\n4B','Qwen\n8B','Llama\n8B']
    panels=[('Internal address signal','native_attention_failure_address','adapted_attention_failure_address','Native','Adapted + restored'),('Ambiguous bridge choice','ambiguous_input_order_address','ambiguous_full_reader_address','Input order','Full reader'),('Composed answers','ambiguous_input_order_em','ambiguous_full_reader_em','Input order','Full reader')]
    for i,(ax,(title,ka,kb,la,lb)) in enumerate(zip(axs,panels)):
        a=[float(lookup[m][ka]) for m in MODELS];b=[float(lookup[m][kb]) for m in MODELS]
        p=ax.bar(x-width/2,a,width,color=GRAY,label=la,zorder=3);q=ax.bar(x+width/2,b,width,color=BLUE if i<2 else '#4D8A71',label=lb,zorder=3)
        ax.bar_label(p,fmt='%.1f',fontsize=6,padding=1.5);ax.bar_label(q,fmt='%.1f',fontsize=6,padding=1.5)
        ax.set_title(f'({chr(97+i)}) {title}',fontsize=7.1,fontweight='bold',pad=18);ax.set_xticks(x,names,fontsize=6.4);ax.set_ylim(0,110);ax.set_yticks([0,50,100]);ax.grid(axis='y',color=GRID,lw=.5,ls='--');ax.spines[['top','right']].set_visible(False);ax.legend(loc='upper center',bbox_to_anchor=(.5,1.16),ncol=2,frameon=False,fontsize=5.8,handlelength=1.1,columnspacing=.6)
    axs[0].set_ylabel('Accuracy (%)',fontsize=6.5)
    save_figure(fig,'data_main_repair_chain_revision')


def make_token_reading_revision():
    """Optional measured replacement panel; absent capture => honest placeholder."""
    path = FIGURE_DATA / 'data_revision_token_capture.json'
    fig = plt.figure(figsize=(3.25,2.47),facecolor='white')
    if not path.exists():
        ax=fig.add_axes([.05,.06,.90,.88]);ax.axis('off')
        ax.text(.5,.88,'Optional token-level mechanism panel',ha='center',fontweight='bold',fontsize=8)
        ax.text(.5,.68,'Awaiting measured attention capture',ha='center',fontsize=7,color='#555555')
        ax.text(.5,.49,'Rebecca Miller bridge:\nAmerican  |  Inge Morath',ha='center',fontsize=7)
        ax.text(.5,.24,'No attention values are inferred.\nUse capture_paired_relation_reading.py to populate this panel.',ha='center',fontsize=6.5,color='#555555')
    else:
        d=read_json('analysis/figure_data/data_revision_token_capture.json')
        if d.get('status')!='MEASURED_READONLY_CAPTURE' or d.get('case_id')!='natural_crossed_3e05970d5c8422f2710d__C12':
            raise ValueError('Measured, matching Angela capture required')
        states=d['states']; keys=[r['state'] for r in states]
        labels={'native_composed':'Native composed','native_direct_same_relation':'Direct mother','native_direct_other_relation':'Direct nationality','adapted_composed':'Adapted composed'}
        if len(keys)<3 or len(set(keys))!=len(keys) or any(k not in labels for k in keys): raise ValueError('Incomplete or unknown states')
        ax=fig.add_axes([.30,.21,.65,.55]); y=np.arange(len(states))[::-1]
        spans=d['span_labels'];names=[spans['other_relation'],spans['target'],'Other bridge tokens'];cols=['#C68B6B','#4D8A71','#CBD5E1']
        start=np.zeros(len(states))
        for n,col in zip(names,cols):
            vals=np.array([100*r['span_weights'][n] if n!='Other bridge tokens' else 100*r['other_weight'] for r in states]);
            if not np.isfinite(vals).all() or np.any(vals < -1e-5): raise ValueError('Invalid measured span weights')
            vals=np.maximum(vals,0);ax.barh(y,vals,left=start,height=.54,color=col,label=n);start+=vals
        if not np.allclose(start,100,atol=.005): raise ValueError('Conditional weights do not sum to 100%')
        ax.set(yticks=y,yticklabels=[labels[k] for k in keys],xlim=(0,100),xticks=[0,50,100],xlabel='Conditional bridge weight (%)');ax.tick_params(labelsize=6,length=0);ax.spines[['top','right','left']].set_visible(False)
        fig.text(.5,.95,'Measured local reading: Rebecca Miller',ha='center',fontweight='bold',fontsize=8)
        fig.text(.5,.86,f"Same {d['head_count']} valid selected heads | final question row",ha='center',fontsize=6.5)
        fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.52,.005),ncol=3,frameon=False,fontsize=5.8,handlelength=1.1,columnspacing=.7)
    save_figure(fig,'data_main_token_reading_optional')


def make_adapted_routing_revision():
    path=FIGURE_DATA/'data_revision_adapted_routing.csv'
    fig=plt.figure(figsize=(6.75,1.89),facecolor='white')
    if not path.exists():
        ax=fig.add_axes([.05,.06,.90,.88]);ax.axis('off')
        ax.text(.5,.78,'Optional post-adaptation routing panel',ha='center',fontweight='bold',fontsize=9)
        ax.text(.5,.51,'Awaiting matched native/adapted paragraph-mass analysis',ha='center',fontsize=7.5)
        ax.text(.5,.28,'No measured values inferred. Run derive_story_adapted_routing.py.',ha='center',fontsize=7,color='#555555')
    else:
        rows=[r for r in _revision_read_rows(path.name) if r['population']=='fixed_native_failures']
        if len(rows)!=6 or len({(r['model'],r['target']) for r in rows})!=6: raise ValueError('Expected six matched model/paragraph records')
        lookup={(r['model'],r['target']):r for r in rows}
        axs=fig.subplots(1,3,sharey=True);fig.subplots_adjust(left=.075,right=.98,top=.73,bottom=.22,wspace=.24)
        for ax,m in zip(axs,MODELS):
            n=[float(lookup[m,t]['native_mass_percent']) for t in ('root','bridge')];a=[float(lookup[m,t]['adapted_mass_percent']) for t in ('root','bridge')];x=np.arange(2);w=.32
            ax.bar_label(ax.bar(x-w/2,n,w,color=GRAY,label='Native'),fmt='%.1f',fontsize=6,padding=1)
            ax.bar_label(ax.bar(x+w/2,a,w,color=BLUE,label='Adapted + restored'),fmt='%.1f',fontsize=6,padding=1)
            ax.set_title(MODEL_NAMES[m],fontsize=7,fontweight='bold');ax.set_xticks(x,['Root','Bridge']);ax.tick_params(labelsize=6);ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color=GRID,lw=.5,ls='--');ax.set_axisbelow(True)
        axs[0].set_ylabel('Attention mass (%)');hi=max(float(r[k]) for r in rows for k in ('native_mass_percent','adapted_mass_percent'));axs[0].set_ylim(0,max(5,hi*1.23));fig.legend(*axs[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.99),ncol=2,frameon=False,fontsize=7)
    save_figure(fig,'data_main_adapted_routing_optional')


def make_story_restoration():
    rows = _revision_read_rows('data_app_ablation_aggregated.csv')
    rec = {(r['model'], r['query'], r['method']): float(r['mean_percent']) for r in rows if r['query'] in ('direct_first','all3')}
    fig, axs = plt.subplots(1, 2, figsize=(3.25, 1.36), sharey=True)
    fig.subplots_adjust(left=.17, right=.94, top=.76, bottom=.25, wspace=.24)
    y = np.arange(3)[::-1]
    for i,(ax,q,title) in enumerate(zip(axs, ('direct_first','all3'), ('(a) First hop','(b) All three'))):
        old = [rec[m,q,'head_tuning'] for m in MODELS]; new = [rec[m,q,'scoped_body'] for m in MODELS]
        for yi,x,z in zip(y,old,new):
            ax.plot([x,z],[yi,yi],color=BLUE,lw=1.6,zorder=2)
            ax.scatter([x],[yi],color=GRAY,s=18,zorder=3); ax.scatter([z],[yi],color=BLUE,s=22,zorder=4)
            ax.annotate(f'+{z-x:.1f}',(z,yi),xytext=(3,0),textcoords='offset points',va='center',fontsize=6.2,fontweight='bold')
        ax.set_title(title,fontsize=7,fontweight='bold',pad=3)
        ax.set(xlim=(15,90),ylim=(-.55,2.55),xticks=[20,40,60,80],yticks=y,yticklabels=['Qwen 4B','Qwen 8B','Llama 8B'])
        ax.tick_params(labelsize=6,length=0,pad=2);ax.grid(axis='x',ls='--',lw=.45,color=GRID);ax.set_axisbelow(True)
        ax.spines[['top','right','left']].set_visible(False)
        ax.set_xlabel('EM (%)',fontsize=6.2,labelpad=2)
    from matplotlib.lines import Line2D
    handles=[Line2D([0],[0],marker='o',color='none',markerfacecolor=GRAY,markeredgecolor=GRAY,markersize=3.8,label='Head tuning'),Line2D([0],[0],marker='o',color='none',markerfacecolor=BLUE,markeredgecolor=BLUE,markersize=3.8,label='+ V/O restoration')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,1.01),ncol=2,frameon=False,fontsize=6.3,columnspacing=.9,handletextpad=.25)
    save_figure(fig,'data_main_restoration_revision')


def make_relation_population_revision():
    """Measured population panel only; no invented values and no pilot aggregation."""
    path = FIGURE_DATA / 'data_revision_relation_reading_summary.csv'
    if not path.exists():
        return
    rows = _revision_read_rows(path.name)
    available = [m for m in MODELS if any(r['model']==m for r in rows)]
    if not available:
        raise ValueError('No measured model in relation summary')
    fig,axs=plt.subplots(1,2,figsize=(6.75,2.18),sharey=False)
    fig.subplots_adjust(left=.12,right=.985,top=.70,bottom=.22,wspace=.30)
    metrics=[('conditional_margin','(a) Within-bridge target preference'),('absolute_margin','(b) Absolute target preference')]
    for ax,(metric,title) in zip(axs,metrics):
        y=np.arange(len(available))[::-1]; offsets=[-.16,.16]
        for oi,(contrast,label,color) in enumerate([('adapted_vs_native','Adapted minus native',BLUE),('same_vs_other_direct','Same minus other direct relation',ORANGE)]):
            for yi,m in zip(y,available):
                matches=[r for r in rows if r['model']==m and r['metric']==metric and r['contrast']==contrast]
                if len(matches)!=1: raise ValueError('Missing unique measured contrast')
                r=matches[0]; est,lo,hi=[float(r[k]) for k in ('estimate_pp','ci95_low_pp','ci95_high_pp')]
                if not np.isfinite([est,lo,hi]).all() or lo>hi: raise ValueError('Bad measured CI')
                ax.plot([lo,hi],[yi+offsets[oi]]*2,color=color,lw=1.2)
                ax.scatter([est],[yi+offsets[oi]],color=color,s=20,zorder=3,label=label if yi==y[0] else None)
        ax.axvline(0,color=GRAY,lw=.7,ls='--');ax.set_title(title,fontsize=7.3,fontweight='bold');ax.set_xlabel('Difference (percentage points)',fontsize=6.7)
        ax.set_yticks(y,[MODEL_NAMES[m] for m in available]);ax.set_ylim(-.48,len(y)-.52);ax.tick_params(labelsize=6);ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',color=GRID,lw=.5,ls='--');ax.set_axisbelow(True)
        left, right = ax.get_xlim()
        ax.set_xticks([tick for tick in ax.get_xticks() if left <= tick <= right])
    fig.legend(*axs[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.98),ncol=2,fontsize=6.8,frameon=False)
    save_figure(fig,'data_main_relation_population_optional')


def make_story_revision():
    style = {"font.family":"DejaVu Sans", "font.size":7, "axes.labelsize":7, "axes.titlesize":8,
             "axes.edgecolor":"#222222", "axes.linewidth":.55, "xtick.labelsize":6.5,
             "ytick.labelsize":6.5, "pdf.fonttype":42, "ps.fonttype":42}
    with plt.rc_context(style):
        make_interaction_revision()
        make_story_teaser()
        make_story_diagnosis()
        make_story_repair()
        make_joint_case_revision()
        make_content_case_revision()
        make_repair_chain_revision()
        make_token_reading_revision()
        make_adapted_routing_revision()
        make_story_restoration()
        make_relation_population_revision()
        make_final_mechanism_figures()
# BEGIN CORETRACE_FINAL_MECHANISM: use only recorded V5 data.
def make_final_mechanism_figures():
    import matplotlib.colors as mcolors
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    data = read_json('analysis/figure_data/data_revision_token_capture.json')
    states = ['native_composed','native_direct_same_relation','native_direct_other_relation','adapted_composed']
    assert data['status']=='MEASURED_READONLY_CAPTURE' and data['head_count']==40
    rec = {r['state']: r for r in data['states']}
    # Three actual spans in the frozen Rebecca Miller paragraph; unshown tokens
    # remain in the conditional denominator. Arthur is an illustrative answer,
    # not the alternate-relation reference span used in the population analysis.
    idx = [26,76,77,89,90,91,92]
    labels = ['American','Arthur','Miller','In','ge','Mor','ath']
    assert [data['tokens'][i].lstrip('\u0120') for i in idx] == labels
    assert data['span_indices']['Inge Morath']==idx[3:] and data['span_indices']['American']==idx[:1]
    a = 100*np.array([[rec[s]['conditional_mean'][i] for i in idx] for s in states])
    if not np.isfinite(a).all() or np.any(a<0): raise ValueError('Bad conditional weights')
    # Use a shared linear scale over all rows, with exact measurements printed.
    fig=plt.figure(figsize=(3.25,1.45)); ax=fig.add_axes([.35,.27,.62,.47]);
    cmap=mcolors.LinearSegmentedColormap.from_list('relation',['#F8FAFC','#CAD9ED','#3D689C'])
    im=ax.imshow(a,aspect='auto',cmap=cmap,vmin=0,vmax=max(12,a.max()))
    for i in range(4):
        for j in range(7):
            ax.text(j,i,f'{a[i,j]:.1f}',ha='center',va='center',fontsize=5.7,color='white' if a[i,j]>8 else INK)
    ax.set_xticks(range(7),labels,fontsize=5.0);
    for j,t in enumerate(ax.get_xticklabels()):
        if j==0: t.set_y(-.055)
    ax.set_yticks(range(4),['Native composed','Direct mother','Direct nationality','Adapted + restored'],fontsize=6.1)
    ax.tick_params(length=0,pad=2); ax.spines[:].set_visible(False)
    ax.axvline(.5,color='white',lw=1.5);ax.axvline(2.5,color='white',lw=1.5)
    ax.add_patch(Rectangle((2.51,-.49),3.98,3.98,fill=False,edgecolor='#437F65',linewidth=1.1))
    fig.text(.5,.94,'Same bridge, different relation queries',ha='center',fontsize=7.4,fontweight='bold')
    fig.text(.5,.835,'Conditional token weights (%)',ha='center',fontsize=6.3)
    fig.text(.35,.045,'Selected spans; normalized over the full bridge',ha='left',fontsize=5.5,color='#555555')
    save_figure(fig,'data_main_relation_tokens_final')

    routing=_revision_read_rows('data_revision_adapted_routing.csv')
    reading=_revision_read_rows('data_revision_relation_reading_summary.csv')
    def row(rows,**keys):
        rr=[r for r in rows if all(r[k]==v for k,v in keys.items())]
        if len(rr)!=1: raise ValueError(f'Nonunique recorded statistic {keys}')
        return rr[0]
    fig,axs=plt.subplots(1,3,figsize=(6.75,1.85)); fig.subplots_adjust(left=.115,right=.985,top=.73,bottom=.23,wspace=.33)
    y=np.arange(3)[::-1]
    def interval(ax,y,r,estimate,lo,hi,col):
        x,l,h=(float(r[k]) for k in (estimate,lo,hi));
        if not np.isfinite([x,l,h]).all() or l>x or h<x: raise ValueError('Bad interval')
        ax.plot([l,h],[y,y],color=col,lw=1.5); ax.scatter(x,y,color=col,s=18,zorder=3)
    for i,(ax,title) in enumerate(zip(axs,['(a) Paragraph access','(b) Conditional preference','(c) Absolute preference'])):
        ax.set_title(title,fontsize=7.1,fontweight='bold');ax.axvline(0,color=GRAY,lw=.6,ls='--');ax.set_yticks(y,['Qwen 4B','Qwen 8B','Llama 8B'] if i==0 else ['','','']);ax.set_ylim(-.52,2.52)
        ax.set_xlabel('Change (pp)',fontsize=6.5); ax.tick_params(length=0,labelsize=6,pad=2); ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',lw=.4,ls='--',color=GRID);ax.set_axisbelow(True)
        if i==0:
            for yi,m,n in zip(y,MODELS,(234,236,243)):
                for off,t,col in [(.15,'root',ORANGE),(-.15,'bridge',BLUE)]:
                    r=row(routing,model=m,population='fixed_native_failures',target=t);assert int(r['n'])==n
                    interval(ax,yi+off,r,'delta_pp','ci95_low_pp','ci95_high_pp',col)
            ax.set_xlim(-3.5,8.0); ax.set_xticks([-3,0,3,6]);
        else:
            metric='conditional_margin' if i==1 else 'absolute_margin'
            for yi,m in zip(y,MODELS):
                for off,c,col in [(-.15,'adapted_vs_native',BLUE),(.15,'same_vs_other_direct',ORANGE)]:
                    r=row(reading,model=m,metric=metric,contrast=c);assert int(r['n_receivers'])==98 and int(r['n_clusters'])==25
                    interval(ax,yi+off,r,'estimate_pp','ci95_low_pp','ci95_high_pp',col)
            ax.set_xlim(-1,33 if i==1 else 19); ax.set_xticks([0,10,20,30] if i==1 else [0,5,10,15]);
    def h(c,l):return Line2D([0],[0],marker='o',lw=1.4,color=c,markersize=3.8,label=l)
    axs[0].legend(handles=[h(ORANGE,'Root'),h(BLUE,'Bridge')],loc='lower center',bbox_to_anchor=(.5,1.18),ncol=2,frameon=False,fontsize=6.2,columnspacing=.8,handlelength=1)
    fig.legend(handles=[h(BLUE,'Adapted + restored minus native'),h(ORANGE,'Same minus other direct relation')],loc='upper right',bbox_to_anchor=(.985,.995),ncol=2,frameon=False,fontsize=6.1,columnspacing=.9,handlelength=1)
    save_figure(fig,'data_main_mechanism_closure_final')
    rows=_revision_read_rows('data_revision_mechanism_repair.csv'); lookup={r['model']:r for r in rows}
    fig,axs=plt.subplots(1,2,figsize=(3.25,1.34),sharey=True);fig.subplots_adjust(left=.22,right=.98,top=.69,bottom=.23,wspace=.18)
    pairs=[('Native','Adapted + restored','native_attention_failure_address','adapted_attention_failure_address','(a) Address readout'),('Order','Reader','ambiguous_input_order_address','ambiguous_full_reader_address','(b) Bridge choice')]
    for i,(ax,(la,lb,ka,kb,title)) in enumerate(zip(axs,pairs)):
        for yi,m in zip(y,MODELS):
            va,vb=float(lookup[m][ka]),float(lookup[m][kb]);ax.plot([va,vb],[yi,yi],color=BLUE,lw=1.3);ax.scatter(va,yi,color=GRAY,s=16,zorder=3);ax.scatter(vb,yi,color=BLUE,s=19,zorder=3)
        ax.set_title(title,fontsize=6.7,fontweight='bold',pad=3);ax.set(xlim=(27,101),ylim=(-.45,2.45),xticks=[30,60,90],yticks=y);ax.set_yticklabels(['Qwen 4B','Qwen 8B','Llama 8B']);ax.tick_params(length=0,labelsize=5.8,pad=1.5);ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',lw=.4,ls='--',color=GRID);ax.set_axisbelow(True);ax.set_xlabel('Accuracy (%)',fontsize=6.0,labelpad=1)
    fig.legend(handles=[Line2D([0],[0],marker='o',color='none',markeredgecolor=GRAY,markerfacecolor=GRAY,label='Native / order',markersize=3.6),Line2D([0],[0],marker='o',color='none',markeredgecolor=BLUE,markerfacecolor=BLUE,label='Adapted / reader',markersize=3.6)],loc='upper center',bbox_to_anchor=(.56,1),ncol=2,frameon=False,fontsize=6,handletextpad=.1,columnspacing=.8)
    save_figure(fig,'data_main_address_signal_final')
# END CORETRACE_FINAL_MECHANISM
# END STORY_REVISION_V5

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only",nargs="*",choices=["composition","diagnosis","causal","content","localization","necessity","ablation","capabilities","ambiguity","case","mechanism_cases","mechanism_causality","joint_rescue","address_routing","mechanism_structure","composition_address","story_revision"])
    args=parser.parse_args();config=read_json("configs/experiments.json");seeds=config["seeds"]
    tasks={"composition":lambda:make_composition(seeds),"diagnosis":lambda:make_diagnosis(seeds),"causal":make_causal,"content":lambda:make_content(seeds),"localization":make_localization,"necessity":make_necessity,"ablation":lambda:make_ablation(seeds),"capabilities":lambda:make_capabilities(seeds),"ambiguity":make_ambiguity,"case":make_case,"mechanism_cases":make_mechanism_cases,"mechanism_causality":make_mechanism_causality,"joint_rescue":make_joint_rescue,"address_routing":make_address_routing,"mechanism_structure":make_mechanism_structure,"composition_address":make_composition_address,"story_revision":make_story_revision}
    requested=list(args.only or tasks)
    # Combined head-profile/knockout panel requires both original collectors.
    if any(name in requested for name in ("localization","necessity")):
        requested=list(dict.fromkeys(requested+["localization","necessity"]))
    collected={name:tasks[name]() for name in requested}
    if "localization" in collected and "necessity" in collected:
        render_head_pair(collected["localization"],*collected["necessity"])
    manifest_name="input_manifest" if not args.only else "input_manifest_"+"_".join(args.only)
    export_csv(manifest_name,[{"path":p,"bytes":(ROOT/p).stat().st_size,"sha256":hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in sorted(INPUT_PATHS)],
               lineterminator="\n" if requested == ["story_revision"] else "\r\n")
    print(f"Read {len(INPUT_PATHS)} input files; see analysis/figure_data/{manifest_name}.csv")

if __name__=="__main__":main()
