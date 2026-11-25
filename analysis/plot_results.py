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
def make_diagnosis(seeds: list[int]) -> None:
    name="data_fig3_diagnosis"
    composition,readouts,overall_readouts=[],[],[]
    subpopulation_file="analysis/internal/readout_validation.json"
    subpopulation_data=read_json(subpopulation_file)
    for model in MODELS:
        filename=source(model,f"seed{seeds[0]}/evaluation/core/summary.json")
        row=unique_record(read_json(filename)["conditional_composition"],method="native")
        denominator=row["both_constituents_correct"]
        composition.append({"model":model,"total_test_sources":row["n_sources"],"both_constituents_correct":denominator,"composition_failures":row["composition_failures"],"composition_successes":denominator-row["composition_failures"],"conditional_failure_percent":100*row["composition_failures"]/denominator,"source":filename})
        overall_file=source(model,"native_readout/complete.json");diagnostic=read_json(overall_file)["diagnostics"]
        population=unique_record(subpopulation_data,directory=source(model,"native_readout"));subgroup=population["native_composition_failure_readout"]
        for features in ("full","attention","metadata"):
            row=subgroup[features]
            if row["n"]!=composition[-1]["composition_failures"]:raise ValueError(f"Composition-failure subpopulation mismatch: {model}/{features}")
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

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only",nargs="*",choices=["diagnosis","causal","content","localization","necessity","ablation","capabilities","ambiguity","case"])
    args=parser.parse_args();config=read_json("configs/experiments.json");seeds=config["seeds"]
    tasks={"diagnosis":lambda:make_diagnosis(seeds),"causal":make_causal,"content":lambda:make_content(seeds),"localization":make_localization,"necessity":make_necessity,"ablation":lambda:make_ablation(seeds),"capabilities":lambda:make_capabilities(seeds),"ambiguity":make_ambiguity,"case":make_case}
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
