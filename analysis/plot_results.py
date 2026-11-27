#!/usr/bin/env python3
"""Publication renderer, preserving the tuned CoReTrace artwork.

--only narrative_revision: render ONLY newly needed panels from archived CSVs.
Other invocations delegate to the previous full renderer, pinned to its verified
Git blob, and then render the additional panels. This preserves every legacy
plotting entry point and the original artwork; no new experiment is run.
All subfigure assembly is performed by the manuscript's native LaTeX layouts.
"""
from pathlib import Path
import csv
import hashlib
from functools import lru_cache
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'paper' / 'figures'
FIGURE_DATA = ROOT / 'analysis' / 'figure_data'
PREVIOUS_COMMIT = '759716c1aae1d50df373cd4d5c1dd4a47fc1ca4a'
PREVIOUS_BLOB = '4f91d449f24432c407ec77777acc6afac1dd4e0f'

# Same constants and publication rcParams as the pinned original, not a new theme.
BLUE, ORANGE, GREEN, PURPLE, RED = '#5E80B8', '#E09063', '#669780', '#9482AC', '#C46D69'
GRAY, LIGHT_GRAY, INK, GRID = '#92979E', '#C9CDD1', '#222222', '#DEDFE0'
MODELS = ('qwen3_4b', 'qwen3_8b', 'llama3_8b')
_PUB_MODEL_SHORT = ['Qwen3-4B', 'Qwen3-8B', 'Llama-3.1-8B']
_PUB_MODEL_TICKS = ['Qwen3\n4B', 'Qwen3\n8B', 'Llama\n8B']
_PUB_STYLE = {
    'font.family': 'serif', 'font.serif': ['Liberation Serif', 'Times New Roman'],
    'mathtext.fontset': 'stix', 'font.size': 8.0, 'axes.labelsize': 8.0,
    'axes.titlesize': 8.0, 'xtick.labelsize': 7.2, 'ytick.labelsize': 7.2,
    'legend.fontsize': 7.5, 'axes.linewidth': .6, 'lines.linewidth': 1.15,
    'lines.markersize': 3.5, 'legend.frameon': False, 'legend.borderaxespad': .15,
    'legend.borderpad': .1, 'legend.handlelength': 1.3, 'legend.handletextpad': .4,
    'legend.columnspacing': .9, 'legend.labelspacing': .25, 'pdf.fonttype': 42,
    'ps.fonttype': 42, 'savefig.facecolor': 'white', 'figure.facecolor': 'white',
    # Inherited defaults from the original base renderer.
    'axes.edgecolor': INK, 'axes.labelcolor': INK, 'text.color': INK,
    'xtick.color': INK, 'ytick.color': INK, 'axes.titleweight': 'normal',
    'axes.facecolor': 'white', 'svg.fonttype': 'none', 'axes.unicode_minus': True,
}

def _read(path):
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def _one(rows, **criteria):
    matches = [r for r in rows if all(r.get(k) == str(v) for k, v in criteria.items())]
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one archived record: {criteria}; got {len(matches)}')
    return matches[0]


def render_narrative_panels():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    import numpy as np

    def axes(width, height, *, left=.43, right=.09, bottom=.32, top=.08):
        # Original _pub_axes geometry and grid treatment.
        fig = plt.figure(figsize=(width, height))
        ax = fig.add_axes([left/width, bottom/height,
                          (width-left-right)/width, (height-bottom-top)/height])
        ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(length=2.2, width=.55, pad=2)
        ax.grid(axis='y', color='#E1E3E5', linewidth=.45, linestyle=(0, (3, 2)))
        ax.set_axisbelow(True)
        return fig, ax

    def save(fig, stem):
        FIGURES.mkdir(parents=True, exist_ok=True)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        for item in fig.findobj(matplotlib.text.Text):
            if not item.get_visible() or not item.get_text():
                continue
            bounds = item.get_window_extent(renderer)
            if np.isfinite(bounds.extents).all() and bounds.width and bounds.height:
                if (bounds.x0 < -.8 or bounds.y0 < -.8 or
                    bounds.x1 > fig.bbox.width+.8 or bounds.y1 > fig.bbox.height+.8):
                    raise ValueError(f'Publication text outside panel {stem}: {item.get_text()}')
        fig.savefig(FIGURES/f'{stem}.pdf', metadata={
            'Creator': 'CoReTrace analysis/plot_results.py', 'CreationDate': None, 'ModDate': None})
        fig.savefig(FIGURES/f'{stem}.png', dpi=300)
        plt.close(fig)

    def key(color):
        return Rectangle((0,0), 1, 1, fc=color, ec='white', lw=.35)

    reading = _read(FIGURE_DATA/'data_revision_relation_reading_summary.csv')
    routing = _read(FIGURE_DATA/'data_revision_adapted_routing.csv')
    addresses = _read(FIGURE_DATA/'data_revision_mechanism_repair.csv')
    core = _read(ROOT/'outputs/tables/tables.csv')

    with plt.rc_context(_PUB_STYLE):
        # Figure 7(b), companion to the original token-level heatmap.
        # Grouped bars, edge widths, confidence intervals, and type sizes match
        # _pub_routing and _pub_appendix_bars in the original renderer.
        fig, ax = axes(3.31, 1.25, left=.49, right=.07, bottom=.28, top=.23)
        xx = np.arange(3)
        metrics = ('conditional_margin', 'per_token_margin', 'absolute_margin')
        colors = (BLUE, ORANGE, GREEN)
        for j, (metric, color) in enumerate(zip(metrics, colors)):
            rr = [_one(reading, model=m, metric=metric, contrast='same_vs_other_direct') for m in MODELS]
            assert all(int(r['n_receivers']) == 98 and int(r['n_clusters']) == 25 for r in rr)
            vals = np.array([float(r['estimate_pp']) for r in rr])
            low = np.array([float(r['ci95_low_pp']) for r in rr])
            high = np.array([float(r['ci95_high_pp']) for r in rr])
            assert np.all(low <= vals) and np.all(vals <= high)
            ax.bar(xx+(j-1)*.24, vals, .215, color=color, ec=INK, lw=.5,
                   yerr=[vals-low,high-vals],
                   error_kw={'elinewidth':.65,'capsize':1.6,'capthick':.65}, zorder=3)
        ax.set(ylim=(0,35),yticks=[0,10,20,30],xticks=xx,xticklabels=_PUB_MODEL_SHORT)
        ax.set_ylabel('Margin change (pp)', labelpad=2)
        fig.legend([key(c) for c in colors], ['Conditional','Per-token','Absolute'],
                   loc='upper center',bbox_to_anchor=(.55,.99),ncol=3,fontsize=7.2)
        save(fig, 'data_main_relation_preference_panel')

        # Figure 10: a column-width reflow of the original three dumbbells.
        # Original color semantics, shaded rows, open/filled endpoints and axes.
        for j,(color,limits,ticks,xlabel) in enumerate(zip(
                (BLUE,ORANGE,GREEN), ((52,108),(0,20),(-3,36)),
                ([60,80,100],[0,10,20],[0,15,30]),
                ('Readout accuracy (%)','Bridge mass (%)','Target - other (pp)'))):
            before,after=[],[]
            for model,n in zip(MODELS,(234,236,243)):
                if j==0:
                    r=_one(addresses,model=model)
                    keys=('native_attention_failure_address','adapted_attention_failure_address')
                elif j==1:
                    r=_one(routing,model=model,population='fixed_native_failures',target='bridge')
                    assert int(r['n'])==n
                    keys=('native_mass_percent','adapted_mass_percent')
                else:
                    r=_one(reading,model=model,metric='conditional_margin',contrast='adapted_vs_native')
                    assert int(r['n_receivers'])==98
                    keys=('native_composed','adapted_composed')
                before.append(float(r[keys[0]]));after.append(float(r[keys[1]]))
            fig,ax=axes(3.25,.97,left=.83,right=.19,bottom=.30,top=.025)
            for y,v0,v1 in zip([2,1,0],before,after):
                ax.axhspan(y-.31,y+.31,facecolor='#F4F6F5',edgecolor='none',zorder=0)
                ax.plot([v0,v1],[y,y],color='#BCCBC5',lw=1.7,zorder=2)
                ax.scatter([v0],[y],s=23,fc='white',ec=GRAY,lw=1.05,zorder=3)
                ax.scatter([v1],[y],s=28,fc=color,ec='white',lw=.45,zorder=3)
                ax.annotate(f'{v0:.1f}',(v0,y),xytext=(-4,0),textcoords='offset points',
                            ha='right',va='center',fontsize=7.5,color='#555B63')
                ax.annotate(f'{v1:.1f}',(v1,y),xytext=(4,0),textcoords='offset points',
                            ha='left',va='center',fontsize=7.5,color=color,fontweight='bold')
            ax.set(xlim=limits,ylim=(-.45,2.55),xticks=ticks,yticks=[2,1,0],yticklabels=_PUB_MODEL_SHORT)
            ax.tick_params(axis='y',length=0,pad=4,labelsize=7.4)
            ax.spines[['top','right','left']].set_visible(False)
            ax.grid(False); ax.grid(axis='x',color='#E0E5E3',lw=.4)
            ax.set_xlabel(xlabel,labelpad=2,fontsize=7.7)
            save(fig, 'data_main_mechanism_closure_col_'+chr(97+j))
        fig=plt.figure(figsize=(3.25,.19))
        fig.legend([Line2D([],[],color=GRAY,marker='o',mfc='white',ls='none',ms=4),
                    Line2D([],[],color=INK,marker='o',ls='none',ms=4)],
                   ['Native',r'Adapted + restored $\mathcal{M}^{*}$ (colored)'],
                   loc='center',ncol=2,fontsize=7.2)
        save(fig,'data_main_mechanism_closure_col_legend')

        # Figure 12(c): compare native/selection baselines to the cumulative
        # adapted configurations without drawing a spurious connection between
        # the baselines and the adaptation path. Retain original model colors.
        methods=('native','native_text','head_tuning','scoped_body','graphfirst','final')
        labels=('Native','Select\nonly','Adapt','+Restore','+Order','+Readout')
        fig,ax=axes(3.25,1.47,left=.45,right=.12,bottom=.38,top=.23)
        for m,color,marker,ls in zip(MODELS,(BLUE,GREEN,RED),('o','s','^'),('-','--',':')):
            rr=[_one(core,model=m,benchmark='core',method=k,query='composed',metric='correct') for k in methods]
            assert all(int(r['n'])==1000 for r in rr)
            vals=100*np.array([float(r['mean_accuracy']) for r in rr])
            err=100*np.array([float(r['sample_std_accuracy'] or 0) for r in rr])
            ax.errorbar([0,1],vals[:2],yerr=err[:2],fmt=marker,ls='none',color=color,
                        ms=3.4,mfc='white',mew=.75,capsize=1.5,elinewidth=.6)
            ax.errorbar(range(2,6),vals[2:],yerr=err[2:],fmt=marker,ls=ls,color=color,
                        ms=3.4,lw=1.15,capsize=1.5,elinewidth=.6)
        ax.set(xlim=(-.32,5.32),ylim=(20,77),yticks=[20,40,60],xticks=range(6),xticklabels=labels)
        ax.tick_params(axis='x',labelsize=7.0,pad=2)
        ax.set_ylabel('Composed EM (%)',labelpad=2)
        fig.legend([Line2D([],[],color=c,marker=mk,ls=ls,ms=3.2) for c,mk,ls in
                    zip((BLUE,GREEN,RED),('o','s','^'),('-','--',':'))],_PUB_MODEL_SHORT,
                   loc='upper center',bbox_to_anchor=(.55,.99),ncol=3,fontsize=7.1)
        save(fig,'data_main_component_path_panel')
    print('Rendered 6 independent publication panels; no original figures overwritten.')


@lru_cache(maxsize=1)
def _original_namespace():
    source = subprocess.check_output(['git','show',f'{PREVIOUS_COMMIT}:analysis/plot_results.py'],cwd=ROOT)
    got = hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()
    if got != PREVIOUS_BLOB:
        raise RuntimeError(f'Unexpected original renderer blob: {got}')
    ns={'__file__':str(Path(__file__).resolve()),'__name__':'_coretrace_preserved_renderer'}
    exec(compile(source,ns['__file__'],'exec'),ns)
    return ns


def __getattr__(name):
    if name.startswith('__'):
        raise AttributeError(name)
    try:
        return _original_namespace()[name]
    except KeyError as exc:
        raise AttributeError(name) from exc


def make_publication_figures():
    _original_namespace()['make_publication_figures']()
    render_narrative_panels()


def main():
    if sys.argv[1:] in (['--only','narrative_revision'], ['--only=narrative_revision']):
        render_narrative_panels()
    else:
        _original_namespace()['main']()
        render_narrative_panels()


if __name__=='__main__':
    main()
