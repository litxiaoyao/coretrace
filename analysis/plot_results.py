#!/usr/bin/env python3
"""Render the final CoReTrace manuscript figures in the original Git checkout.

The existing numerical pipeline is loaded from its immutable, verified Git blob;
the publication renderers below export independent vector panels and native
LaTeX subcaptions from released measurements. The original analysis functions
remain available and require the repository's baseline commit locally. No model
execution or network access is required. Standalone previews use pdfLaTeX.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

_BASE_COMMIT = "4990754cb73512599adfea9519862868b4260dbf"
_BASE_BLOB = "eb94fb5a81105306b4c2cadbf687c66e91a5668d"
_ROOT = Path(__file__).resolve().parents[1]
try:
    _base_source = subprocess.check_output(
        ["git", "show", f"{_BASE_COMMIT}:analysis/plot_results.py"], cwd=_ROOT
    )
except (FileNotFoundError, subprocess.CalledProcessError) as exc:
    raise RuntimeError(
        "The original CoReTrace Git history is required. Use a checkout "
        "containing commit " + _BASE_COMMIT + "."
    ) from exc
if hashlib.sha1(f"blob {len(_base_source)}\0".encode() + _base_source).hexdigest() != _BASE_BLOB:
    raise RuntimeError("Unexpected original plotting source; refusing to run.")
_original_name = __name__
try:
    __name__ = "_coretrace_base_plot_results"
    exec(compile(_base_source, str(Path(__file__).resolve()), "exec"), globals())
finally:
    __name__ = _original_name

# Keep the original output writer for the final renderers. Superseded legacy
# plots must not overwrite the manuscript figures or author-selected artwork.
_base_save_figure = save_figure
_FINAL_STEMS = frozenset({'data_main_relation_tokens_final', 'figure2_diagnosis_revision', 'figure1_teaser_revision', 'data_main_composition_address', 'data_main_localization', 'data_main_address_routing', 'data_main_interaction_revision', 'figure3_method_revision', 'data_main_joint_case_revision', 'data_main_mechanism_closure_final', 'data_main_address_signal_final', 'data_main_head_causality'})


def _save_legacy_figure(fig, name):
    if name in _FINAL_STEMS:
        plt.close(fig)
        return
    return _base_save_figure(fig, name)


save_figure = _save_legacy_figure

# BEGIN CORETRACE_STORY_POLISH: recorded experiments only.
def make_story_polish():
    """Refresh the teaser and key mechanism figures from archived measurements."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    from matplotlib.colors import LinearSegmentedColormap
    cases = _story_cases()
    factors = _revision_read_rows('data_fig4_causal_factorial.csv')
    contrasts = _revision_read_rows('data_fig4_causal_factorial_contrasts.csv')
    addresses = _revision_read_rows('data_revision_mechanism_repair.csv')
    lookup = {(r['model'], r['method']):float(r['accuracy_percent']) for r in factors}
    ci = {r['model']: [float(r[k]) for k in ('estimate_pp','CI95_low_pp','CI95_high_pp')]
          for r in contrasts if r['contrast']=='interaction'}
    native_label = '#7B8490'
    dark_blue, dark_orange, dark_green = '#346A9D', '#B76736', '#3C8067'
    pale_blue, pale_orange, pale_green = '#EFF5FB', '#FCF2E8', '#EDF7F1'
    names = ['Qwen3-4B','Qwen3-8B','Llama-3.1-8B']
    style = {'font.family':'DejaVu Sans','font.size':7.0,'axes.labelsize':7.0,
             'axes.titlesize':8,'xtick.labelsize':6.6,'ytick.labelsize':6.6,
             'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42}
    with plt.rc_context(style):
        # Author-selected conceptual teaser; keep the cropped PNG as the editable source.
        teaser = FIGURES / 'figure1_teaser_revision.png'
        INPUT_PATHS.add(teaser.relative_to(ROOT).as_posix())
        image = plt.imread(teaser)
        height, width = image.shape[:2]
        fig = plt.figure(figsize=(3.25, 3.25 * height / width), frameon=False)
        ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(image, interpolation='none')
        ax.set_axis_off()
        fig.savefig(FIGURES / 'figure1_teaser_revision.pdf', dpi=width/3.25,
                    metadata={'Creator': 'CoReTrace: author-selected conceptual artwork'})
        plt.close(fig)

        # Aligned analytical and repair frameworks. The three functional labels
        # describe quantities of a shared head set, not an inferred layer order.
        def framework_canvas(height):
            fig = plt.figure(figsize=(6.75, height))
            ax = fig.add_axes([0, 0, 1, 1]); ax.set(xlim=(0,100), ylim=(0,100)); ax.axis('off')
            return fig, ax

        def panel(ax, x, y, w, h, title, detail, edge, fill, title_fs=7.6, detail_fs=6.7):
            ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.12,rounding_size=1.05',ec=edge,fc=fill,lw=.85))
            ax.text(x+w/2,y+h*.76,title,ha='center',va='center',color=edge,fontsize=title_fs,fontweight='bold')
            if detail:
                ax.text(x+w/2,y+h*.34,detail,ha='center',va='center',fontsize=detail_fs,linespacing=1.2)

        def conn(ax,x1,y1,x2,y2,color=native_label,arrow=True,ls='-'):
            ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>' if arrow else '-',mutation_scale=7.5,color=color,lw=.9,linestyle=ls,shrinkA=0,shrinkB=0))

        # Figure 2: author-selected conceptual artwork. Keep the PNG unchanged.
        diagnosis = FIGURES / 'figure2_diagnosis_revision.png'
        INPUT_PATHS.add(diagnosis.relative_to(ROOT).as_posix())
        image = plt.imread(diagnosis)
        height, width = image.shape[:2]
        fig = plt.figure(figsize=(6.75, 6.75 * height / width), frameon=False)
        ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(image, interpolation='none')
        ax.set_axis_off()
        fig.savefig(FIGURES / 'figure2_diagnosis_revision.pdf', dpi=width/6.75,
                    metadata={'Creator': 'CoReTrace: author-selected conceptual artwork'})
        plt.close(fig)
        grayfill='#F3F5F7'

        # Figure 3: author-selected conceptual artwork; the original PNG is retained.
        repair = FIGURES / 'figure3_method_revision.png'
        INPUT_PATHS.add(repair.relative_to(ROOT).as_posix())
        image = plt.imread(repair)
        height, width = image.shape[:2]
        fig = plt.figure(figsize=(6.75, 6.75 * height / width), frameon=False)
        ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(image, interpolation='none')
        ax.set_axis_off()
        fig.savefig(FIGURES / 'figure3_method_revision.pdf', dpi=width/6.75,
                    metadata={'Creator': 'CoReTrace: author-selected conceptual artwork'})
        plt.close(fig)

        # Frozen selected head locations across the three model architectures.
        membership=_revision_read_rows('data_app_head_membership.csv')
        profiles=_revision_read_rows('data_app_localization_layer_profiles.csv')
        fig,axs=plt.subplots(1,3,figsize=(3.25,1.33),sharey=True)
        fig.subplots_adjust(left=.13,right=.985,top=.69,bottom=.23,wspace=.24)
        for ax,m,name,count in zip(axs,MODELS,['Qwen3-4B','Qwen3-8B','Llama-8B'],[20,20,40]):
            heads=[r for r in membership if r['model']==m and int(r['ranked'])==1]
            dims=[r for r in profiles if r['model']==m]
            nl=max(int(r['layer']) for r in dims)+1; nh=int(dims[0]['heads_per_layer'])
            assert len(heads)==count and len({(r['layer'],r['head']) for r in heads})==count
            ax.add_patch(Rectangle((-.5,-.5),nh,nl,fc='#F4F6F8',ec='#D2D7DB',lw=.5))
            for row in heads:
                l,h=int(row['layer']),int(row['head']);assert 0<=l<nl and 0<=h<nh
                ax.add_patch(Rectangle((h-.48,l-.48),.96,.96,fc=dark_blue if int(row['direct']) else native_label,ec='none'))
            ax.set(xlim=(-.5,nh-.5),ylim=(35.5,-.5),xticks=[0,15,31],yticks=[0,12,24,35]);ax.set_title(name,fontsize=6.5,pad=2,fontweight='bold');ax.tick_params(length=1.2,labelsize=5.5,pad=1);ax.spines[['top','right','left','bottom']].set_visible(False);ax.set_xlabel('Head',fontsize=5.8,labelpad=1)
        axs[0].set_ylabel('Layer',fontsize=6.2,labelpad=2)
        fig.legend(handles=[Rectangle((0,0),1,1,fc=dark_blue,label='Selected + direct top-$k$'),Rectangle((0,0),1,1,fc=native_label,label='Selected only')],loc='upper center',bbox_to_anchor=(.52,.995),ncol=2,frameon=False,fontsize=5.5,handlelength=.75,columnspacing=.8,handletextpad=.4)
        save_figure(fig,'data_main_localization')

        # Actual token weights aggregated into interpretable fact spans.
        data=read_json('analysis/figure_data/data_revision_token_capture.json')
        assert data['status']=='MEASURED_READONLY_CAPTURE' and data['head_count']==40
        idx=[[26],[76,77],[89,90,91,92]]
        assert data['span_indices']['Inge Morath']==idx[2] and data['span_indices']['American']==idx[0]
        assert [data['tokens'][i].lstrip('\u0120') for i in idx[0]+idx[1]+idx[2]]==['American','Arthur','Miller','In','ge','Mor','ath']
        states=['native_composed','native_direct_same_relation','native_direct_other_relation','adapted_composed']
        rec={r['state']:r for r in data['states']}
        a=100*np.array([[sum(rec[s]['conditional_mean'][i] for i in span) for span in idx] for s in states])
        assert np.isfinite(a).all() and (a>=0).all()
        fig=plt.figure(figsize=(3.25,1.45)); ax=fig.add_axes([.36,.22,.61,.58]);
        cmap=LinearSegmentedColormap.from_list('fact_weights',['#F5F8FC','#B7CFE6','#346A9D'])
        vmax=max(30,a.max()); ax.imshow(a,aspect='auto',cmap=cmap,vmin=0,vmax=vmax)
        for i in range(4):
            for j in range(3):
                ax.text(j,i,f'{a[i,j]:.1f}',ha='center',va='center',fontsize=7.0,color='white' if a[i,j]>vmax*.58 else INK,fontweight='bold' if j==2 else 'normal')
        ax.set_xticks(range(3),['American\n(nationality)','Arthur Miller\n(father)','Inge Morath\n(mother)'],fontsize=5.7)
        ax.set_yticks(range(4),['Native composed','Direct mother','Direct nationality','Adapted + restored'],fontsize=6.0)
        ax.tick_params(length=0,pad=2); ax.spines[:].set_visible(False)
        ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,4,1),minor=True);ax.grid(which='minor',color='white',lw=1.1)
        ax.tick_params(which='minor',length=0)
        ax.add_patch(Rectangle((1.51,-.49),.98,3.98,fill=False,edgecolor=dark_green,lw=1.0))
        fig.text(.5,.985,r'Read ($\rho$): Rebecca Miller, same bridge',ha='center',va='top',fontsize=7.0,fontweight='bold')
        fig.text(.97,.865,'Conditional weight (%)',ha='right',fontsize=6.0)
        save_figure(fig,'data_main_relation_tokens_final')

        # Figure 10: one low-height horizontal row of model-specific slope plots.
        fig,axs=plt.subplots(1,3,figsize=(6.75,1.60),sharey=True)
        fig.subplots_adjust(left=.072,right=.987,top=.70,bottom=.18,wspace=.18)
        for ax,model in zip(axs,MODELS):
            n=[lookup[(model,k)] for k in ('native','conditional_only')]
            b=[lookup[(model,k)] for k in ('mass_only','both')]
            ax.plot([0,1],n,'o-',color=native_label,label=r'Native access $m$',lw=1.45,ms=3.7)
            ax.plot([0,1],b,'o-',color=dark_orange,label=r'Calibrated access $\tau$',lw=1.7,ms=3.7)
            for j,y0 in enumerate(n): ax.annotate(f'{y0:.0f}',(j,y0),xytext=(0,-9),textcoords='offset points',ha='center',color='#555B63',fontsize=6.4)
            for j,y0 in enumerate(b): ax.annotate(f'{y0:.0f}',(j,y0),xytext=(0,4),textcoords='offset points',ha='center',color=dark_orange,fontsize=6.4,fontweight='bold')
            # The effects of pattern transfer are shown directly beside the slopes.
            ax.annotate(f'{n[1]-n[0]:+.0f} pp',(.5,sum(n)/2),xytext=(0,-9),textcoords='offset points',ha='center',color='#555B63',fontsize=6.2)
            ax.annotate(f'{b[1]-b[0]:+.0f} pp',(.5,sum(b)/2),xytext=(0,4),textcoords='offset points',ha='center',color=dark_orange,fontsize=6.2,fontweight='bold')
            est,lo,hi=ci[model]; assert np.isclose((b[1]-b[0])-(n[1]-n[0]),est)
            ax.set_title(f'{MODEL_NAMES[model]}  |  I={est:+.0f} [{lo:.0f}, {hi:.0f}]',fontsize=7.0,fontweight='bold',pad=4)
            ax.set_xticks([0,1],[r'Native $\rho$',r'Direct $\rho^{\rm dir}$']);ax.set(xlim=(-.20,1.20),ylim=(13,96),yticks=[20,40,60,80])
            ax.tick_params(length=1.7,pad=1.7,labelsize=6.4)
            ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color=GRID,lw=.5,ls='--');ax.set_axisbelow(True)
        axs[0].set_ylabel('Composed EM (%)',fontsize=7,labelpad=2);h,l=axs[0].get_legend_handles_labels()
        fig.legend(h,l,loc='upper center',bbox_to_anchor=(.5,.999),ncol=2,frameon=False,fontsize=6.9)
        save_figure(fig,'data_main_interaction_revision')

        # Mechanistic closure: directly align all three functional quantities.
        # Address recovery uses separately fitted attention-only readouts on the
        # fixed native-failure population, as does the canonical routing analysis.
        # Relation preferences are measured on the distinct 98 discovery receivers.
        routing=_revision_read_rows('data_revision_adapted_routing.csv')
        reading=_revision_read_rows('data_revision_relation_reading_summary.csv')
        def one(rows,**criteria):
            matched=[r for r in rows if all(r[k]==v for k,v in criteria.items())]
            assert len(matched)==1,criteria
            return matched[0]
        fig,axs=plt.subplots(1,3,figsize=(6.75,1.85),sharey=True)
        fig.subplots_adjust(left=.14,right=.98,top=.72,bottom=.22,wspace=.29)
        y=np.arange(3)[::-1]
        titles=[r'(a) Locate: address',r'(b) Route: bridge $m$',r'(c) Read: conditional $\rho$']
        xlimits=[(55,100),(0,17),(0,31)]
        xticks=[[60,75,90],[0,5,10,15],[0,10,20,30]]
        for j,ax in enumerate(axs):
            col=[dark_blue,dark_orange,dark_green][j]
            for yi,m,ncase in zip(y,MODELS,(234,236,243)):
                if j==0:
                    r=one(addresses,model=m)
                    v0,v1=float(r['native_attention_failure_address']),float(r['adapted_attention_failure_address'])
                elif j==1:
                    r=one(routing,model=m,population='fixed_native_failures',target='bridge');assert int(r['n'])==ncase
                    v0,v1=float(r['native_mass_percent']),float(r['adapted_mass_percent'])
                else:
                    r=one(reading,model=m,metric='conditional_margin',contrast='adapted_vs_native');assert int(r['n_receivers'])==98 and int(r['n_clusters'])==25
                    v0,v1=float(r['native_composed']),float(r['adapted_composed'])
                assert v1>v0
                ax.plot([v0,v1],[yi,yi],color=col,lw=1.8,zorder=2)
                ax.scatter([v0],[yi],color=native_label,s=19,zorder=3);ax.scatter([v1],[yi],color=col,s=25,zorder=3)
                ax.annotate(f'{v0:.1f}',(v0,yi),xytext=(-2,5),textcoords='offset points',ha='right',fontsize=6.1,color='#555B63')
                ax.annotate(f'{v1:.1f}',(v1,yi),xytext=(3,5),textcoords='offset points',ha='left',fontsize=6.1,color=col,fontweight='bold')
            ax.set_title(titles[j],fontweight='bold',fontsize=7.4,pad=5,color=col)
            ax.set(xlim=xlimits[j],ylim=(-.45,2.50),yticks=y,xticks=xticks[j]);ax.set_yticklabels(names)
            ax.tick_params(length=0,labelsize=6.5,pad=2);ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',color=GRID,lw=.5,ls='--');ax.set_axisbelow(True)
            ax.set_xlabel(['Readout accuracy (%)','Mass (%)','Target − other (pp)'][j],fontsize=6.5,labelpad=2)
        fig.text(.5,.965,r'Gray: native  |  Colored endpoint: adapted + restored $\mathcal{M}^*$',ha='center',va='top',fontsize=7)
        save_figure(fig,'data_main_mechanism_closure_final')

        # Figure 14: the recovered address is useful in actual ambiguous inputs.
        # Both bridge choice and downstream composed EM are from the same 103
        # ambiguous-input population in the existing recorded selection audit.
        fig,axs=plt.subplots(1,2,figsize=(3.25,1.34),sharey=True)
        fig.subplots_adjust(left=.24,right=.985,top=.68,bottom=.23,wspace=.19)
        for j,(ax,ka,kb,title) in enumerate(zip(axs,
                ['ambiguous_input_order_address','ambiguous_input_order_em'],
                ['ambiguous_full_reader_address','ambiguous_full_reader_em'],
                ['(a) Bridge choice','(b) Composed EM'])):
            for yi,m in zip(y,MODELS):
                row=one(addresses,model=m);v0,v1=float(row[ka]),float(row[kb])
                ax.plot([v0,v1],[yi,yi],color=dark_blue,lw=1.35)
                ax.scatter([v0],[yi],color=native_label,s=16,zorder=3);ax.scatter([v1],[yi],color=dark_blue,s=19,zorder=3)
            ax.set_title(title,fontsize=6.8,fontweight='bold',color=dark_blue,pad=3)
            ax.set(xlim=(25,101),ylim=(-.45,2.45),xticks=[30,60,90],yticks=y)
            ax.set_yticklabels(['Qwen 4B','Qwen 8B','Llama 8B']);ax.tick_params(length=0,labelsize=5.8,pad=1.5)
            ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',lw=.4,ls='--',color=GRID);ax.set_axisbelow(True)
            ax.set_xlabel('Accuracy (%)',fontsize=6.0,labelpad=1)
        fig.legend(handles=[Line2D([0],[0],marker='o',color='none',markeredgecolor=native_label,markerfacecolor=native_label,label='Input order',markersize=3.6),Line2D([0],[0],marker='o',color='none',markeredgecolor=dark_blue,markerfacecolor=dark_blue,label='Address reader',markersize=3.6)],loc='upper center',bbox_to_anchor=(.56,.995),ncol=2,frameon=False,fontsize=6,handletextpad=.1,columnspacing=.8)
        save_figure(fig,'data_main_address_signal_final')
        # Figure 7: two knockout panels reflowed to the native column width.
        # Keep all three models and every measured dose, including zero.
        knockout = _revision_read_rows('data_main_head_causality.csv')
        kval = {(r['model'],r['query'],r['selection'],int(r['knocked_out'])):float(r['accuracy_percent']) for r in knockout}
        assert len(kval)==42 and all(int(r['n'])==1000 for r in knockout)
        fig, axs = plt.subplots(1,2,figsize=(3.25,1.72))
        fig.subplots_adjust(left=.115,right=.984,top=.70,bottom=.20,wspace=.34)
        doses=[0,20,40,80]
        markers=['o','s','^']; styles=['-','--',':']
        colors=[dark_orange,native_label]
        for ax,query,title,ylim,yt in zip(axs,['composed','direct_target'],['(a) Composed','(b) Direct second hop'],[(0,40),(0,65)],[[0,10,20,30,40],[0,20,40,60]]):
            for i,model in enumerate(MODELS):
                for group,color in zip(['selected','random'],colors):
                    vals=[kval[model,query,'native',0]]+[kval[model,query,group,d] for d in doses[1:]]
                    ax.plot(doses,vals,ls=styles[i],marker=markers[i],ms=3.0,lw=.85,color=color,mfc=color if group=='selected' else 'white',mew=.65)
            ax.set(xlim=(-4,84),ylim=ylim,xticks=doses,yticks=yt)
            ax.set_title(title,fontsize=6.8,fontweight='bold',pad=3)
            ax.tick_params(labelsize=6.1,length=2,pad=1.5); ax.spines[['top','right']].set_visible(False)
            ax.grid(axis='y',ls='--',color=GRID,lw=.45); ax.set_axisbelow(True)
        axs[0].set_ylabel('EM (%)',fontsize=6.4,labelpad=2)
        fig.text(.55,.025,'Heads removed',ha='center',va='bottom',fontsize=6.5)
        fig.legend(handles=[Line2D([0],[0],color=dark_orange,lw=1.2,label='Ranked'),Line2D([0],[0],color=native_label,lw=1.2,label='Layer-matched random')],loc='upper center',bbox_to_anchor=(.53,.995),ncol=2,fontsize=6.4,frameon=False,columnspacing=1,handlelength=1.5)
        fig.legend(handles=[Line2D([0],[0],color=INK,ls=ls,marker=mk,ms=3,label=label) for ls,mk,label in zip(styles,markers,['Qwen 4B','Qwen 8B','Llama 8B'])],loc='upper center',bbox_to_anchor=(.53,.875),ncol=3,fontsize=6.0,frameon=False,columnspacing=.75,handlelength=1.7,handletextpad=.35)
        save_figure(fig,'data_main_head_causality')
        # Figure 8: use the space released by Figure 7 for a legible three-panel
        # routing analysis; all plotted estimates/intervals are archived values.
        allrows=_revision_read_rows('data_main_address_routing_all_sources.csv')
        massrows=_revision_read_rows('data_main_address_routing_mass.csv')
        condrows=_revision_read_rows('data_main_address_routing_conditional.csv')
        fig,axs=plt.subplots(1,3,figsize=(6.75,1.86))
        fig.subplots_adjust(left=.074,right=.987,top=.69,bottom=.22,wspace=.32)
        xx=np.arange(3); barw=.24
        methods=['oracle_second_paragraph','oracle_first_paragraph','lengthmatched_other_paragraph']
        labels=['Bridge','Root','Other']; cols=['#5E80B8','#E09063','#92979E']
        def getv(rows,model,**keys):
            rr=[r for r in rows if r['model']==model and all(r[k]==v for k,v in keys.items())];assert len(rr)==1
            return rr[0]
        for j,(ax,title) in enumerate(zip(axs,['(a) Destination controls','(b) Native allocation','(c) Routing repair'])):
            ax.set_title(title,fontsize=7.5,fontweight='bold',pad=4)
            ax.set_xticks(xx,['Qwen 4B','Qwen 8B','Llama 8B'] if j==0 else ['Qwen 4B\n$n=169$','Qwen 8B\n$n=174$','Llama 8B\n$n=209$'])
            ax.tick_params(labelsize=6.4,length=1.8,pad=1.5); ax.spines[['top','right']].set_visible(False)
            ax.grid(axis='y',ls='--',color=GRID,lw=.45);ax.set_axisbelow(True)
            if j in (0,2):
                field,lo,hi=('delta_pp','CI95_low_pp','CI95_high_pp') if j==0 else ('repair_percent','CI95_low_percent','CI95_high_percent')
                rows=allrows if j==0 else condrows
                for k,(method,col) in enumerate(zip(methods,cols)):
                    rr=[getv(rows,m,method=method) for m in MODELS];vals=np.array([float(r[field]) for r in rr]);low=np.array([float(r[lo]) for r in rr]);high=np.array([float(r[hi]) for r in rr]);pos=xx+(k-1)*barw
                    ax.bar(pos,vals,barw*.90,color=col,edgecolor=INK,lw=.78,yerr=[vals-low,high-vals],error_kw={'elinewidth':.85,'capsize':2.0,'capthick':.75,'ecolor':INK},zorder=3)
                    if j==2:
                        for x,v,r,h in zip(pos,vals,rr,high):ax.text(x,h+2.0,r['corrected'],ha='center',va='bottom',fontsize=6.2,fontweight='bold' if k==0 else 'normal')
                if j==0:ax.axhline(0,color=INK,lw=.7);ax.set(ylim=(-27,23),yticks=[-20,-10,0,10,20],ylabel='EM change (pp)')
                else:ax.set(ylim=(0,66),yticks=[0,15,30,45,60],ylabel='Repaired (%)')
            else:
                for k,(role,col) in enumerate(zip(['root','bridge'],[cols[1],cols[0]])):
                    vals=[float(getv(massrows,m,role=role)['attention_mass_percent']) for m in MODELS];pos=xx+(k-.5)*.31
                    ax.bar(pos,vals,.28,color=col,edgecolor=INK,lw=.78,zorder=3)
                    for x,v in zip(pos,vals):ax.text(x,v+1.0,f'{v:.1f}',ha='center',va='bottom',fontsize=6.2)
                ax.set(ylim=(0,40),yticks=[0,10,20,30],ylabel='Attention mass (%)')
            ax.yaxis.label.set_size(7.0)
        fig.legend(handles=[Rectangle((0,0),1,1,facecolor=c,edgecolor=INK,lw=.78,label=l) for l,c in zip(labels,cols)],loc='upper center',bbox_to_anchor=(.5,.995),ncol=3,fontsize=7.1,frameon=False,columnspacing=1.5)
        save_figure(fig,'data_main_address_routing')
        # Publication bar style: solid muted fills, one dark external outline,
        # and a single dark seam for touching segments. The full-width base
        # underneath the second fill prevents antialiasing from exposing white.
        bar_blue,bar_orange,bar_gray='#5E80B8','#E09063','#C9CDD1'
        stroke='#222222'; bar_lw=.78
        def outlined_stack(ax, y, split, total, colors, height=.65):
            assert 0 <= split <= total
            ax.barh(y,total,height=height,color=colors[0],edgecolor='none',zorder=3)
            ax.barh(y,total-split,left=split,height=height,color=colors[1],edgecolor='none',zorder=3)
            ax.add_patch(Rectangle((0,y-height/2),total,height,facecolor='none',edgecolor=stroke,
                                   linewidth=bar_lw,joinstyle='miter',zorder=4,clip_on=False))
            if 0 < split < total:
                ax.plot([split,split],[y-height/2,y+height/2],color=stroke,lw=bar_lw,
                        solid_capstyle='butt',zorder=4)
        def bar_key(color,label):
            return Rectangle((0,0),1,1,facecolor=color,edgecolor=stroke,linewidth=bar_lw,label=label)
        def bar_axis(ax, axis='y'):
            ax.spines[['top','right']].set_visible(False)
            ax.spines['bottom'].set_linewidth(.75);ax.spines['left'].set_linewidth(.75)
            ax.tick_params(length=2.5,width=.65,pad=2,labelsize=6.5)
            ax.grid(axis=axis,ls='--',color='#E0E0E0',lw=.5);ax.set_axisbelow(True)
        # Figure 4: same conditional population and readout data, no re-estimation.
        cr=_revision_read_rows('data_main_composition_address_composition.csv')
        rr=_revision_read_rows('data_main_composition_address_readout.csv')
        fig=plt.figure(figsize=(6.75,1.90))
        fig.text(.020,.985,'(a) Correct hops, failed composition',ha='left',va='top',fontsize=7.3,fontweight='bold')
        fig.text(.520,.985,'(b) Bridge addresses in those failures',ha='left',va='top',fontsize=7.3,fontweight='bold')
        left=fig.add_axes([.145,.270,.320,.445]);bar_axis(left,'x')
        y=np.arange(len(MODELS))[::-1]
        rows=[next(r for r in cr if r['model']==m) for m in MODELS]
        for yi,r in zip(y,rows):
            n,ok,bad=(int(r[k]) for k in ('both_constituents_correct','composition_successes','composition_failures'))
            assert ok+bad==n and np.isclose(100*bad/n,float(r['conditional_failure_percent']))
            p=100*ok/n;outlined_stack(left,yi,p,100,(bar_blue,bar_orange),.66)
            left.text(p/2,yi,f'{ok} ({p:.1f}%)',ha='center',va='center',fontsize=6.0,color='white',fontweight='bold',zorder=5)
            left.text((p+100)/2,yi,f'{bad} ({100-p:.1f}%)',ha='center',va='center',fontsize=6.0,color=stroke,fontweight='bold',zorder=5)
        left.set(yticks=y,yticklabels=[f"{MODEL_NAMES[m]}\n$n={r['both_constituents_correct']}$" for m,r in zip(MODELS,rows)],xlim=(0,100),ylim=(-.55,2.55),xticks=[0,50,100],xlabel='Share of constituent-correct sources (%)')
        left.spines['left'].set_visible(False);left.tick_params(axis='y',length=0,pad=4,labelsize=6.0);left.tick_params(axis='x',labelsize=6.2);left.xaxis.label.set_size(6.0)
        fig.legend(handles=[bar_key(bar_blue,'Composed correct'),bar_key(bar_orange,'Composed incorrect')],loc='upper center',bbox_to_anchor=(.290,.855),ncol=2,frameon=False,fontsize=6.0,handlelength=1.3,handletextpad=.4,columnspacing=.9)
        right=fig.add_axes([.590,.270,.385,.445]);bar_axis(right)
        x=np.arange(len(MODELS));width=.23
        def readrow(model,feature):
            matching=[r for r in rr if r['model']==model and r['feature_set']==feature];assert len(matching)==1
            r=matching[0];assert int(r['n'])==int(next(c for c in cr if c['model']==model)['composition_failures'])
            assert np.isclose(float(r['accuracy_percent']),100*int(r['correct'])/int(r['n']))
            return r
        for j,(feature,label,color) in enumerate((('metadata','Metadata',bar_gray),('attention','Attention',bar_blue),('full','Full',bar_orange))):
            vals=[float(readrow(m,feature)['accuracy_percent']) for m in MODELS];pos=x+(j-1)*width
            right.bar(pos,vals,width,color=color,edgecolor=stroke,linewidth=bar_lw,zorder=3)
            if feature=='full':
                for a,b in zip(pos,vals):right.text(a,b+2,f'{b:.1f}',ha='center',va='bottom',fontsize=6.1)
        right.set(xticks=x,xticklabels=[f"{short}\n$n={readrow(m,'full')['n']}$" for short,m in zip(['Qwen3\n4B','Qwen3\n8B','Llama\n8B'],MODELS)],ylim=(0,112),yticks=[0,50,100],ylabel='Bridge-address accuracy (%)')
        right.tick_params(labelsize=6.0);right.yaxis.label.set_size(6.1)
        fig.legend(handles=[bar_key(c,l) for c,l in [(bar_gray,'Metadata'),(bar_blue,'Attention'),(bar_orange,'Full')]],loc='upper center',bbox_to_anchor=(.780,.855),ncol=3,frameon=False,fontsize=6.0,handlelength=1.3,handletextpad=.4,columnspacing=.9)
        save_figure(fig,'data_main_composition_address')

        # Figure 11: preserve the actual receiver and four recorded answers;
        # use the same outlined stacks for the existing joint-correction counts.
        case=cases['angela']; jointrows=_revision_read_rows('data_revision_joint_counts.csv')
        fig=plt.figure(figsize=(3.25,2.47)); ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,100),ylim=(0,100));ax.axis('off')
        def case_box(x,y,w,h,title,detail,color,fill,fs=6.6):
            ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.15,rounding_size=1.1',facecolor=fill,edgecolor=color,lw=.8))
            ax.text(x+w/2,y+h*.64,title,ha='center',va='center',fontsize=fs,fontweight='bold',color=INK)
            ax.text(x+w/2,y+h*.28,detail,ha='center',va='center',fontsize=fs-.7,color=INK)
        ax.text(1,99,'(a) A joint-only repair in Llama-3.1-8B',ha='left',va='top',fontsize=7.4,fontweight='bold')
        ax.text(2,88,'Q: Who is the mother of the director of Angela?',ha='left',fontsize=6.6)
        case_box(2,72,34,12,'P7: Angela','directed by Rebecca Miller',bar_orange,'#FCF0E6',6.4)
        conn(ax,36,78,41,78,bar_blue)
        case_box(41,72,57,12,'P5: Rebecca Miller','daughter of Arthur Miller and Inge Morath',bar_blue,'#F0F4FA',6.1)
        for i,r in enumerate(case['arms']):
            xx=2+(i%2)*49;yy=53-(i//2)*15
            name={'native':'Native','mass_only':'Mass only','conditional_only':'Pattern only','both':'Both'}[r['method']]
            color='#4D8A71' if r['correct'] else '#B86A67';fill='#EDF6F1' if r['correct'] else '#FBEFEE'
            case_box(xx,yy,47,12,name,r['answer']+('  (correct)' if r['correct'] else ''),color,fill)
        ax.text(1,33,'(b) Joint-only corrections across models',ha='left',va='top',fontsize=7.4,fontweight='bold')
        bar=fig.add_axes([.23,.098,.73,.163]);bar.spines[['top','right','left','bottom']].set_visible(False)
        vals={r['model']:r for r in jointrows}
        for yi,m in zip(y,MODELS):
            j,t,n=(int(vals[m][k]) for k in ('joint_only','both_repairs','native_errors'));assert 0<=j<=t<=n
            outlined_stack(bar,yi,j,t,(bar_orange,bar_gray),.64)
            bar.text(j/2,yi,str(j),ha='center',va='center',fontsize=6.4,fontweight='bold',zorder=5)
            bar.text(t+.6,yi,str(t),ha='left',va='center',fontsize=6.2,zorder=5)
        bar.set(yticks=y,yticklabels=['Qwen 4B','Qwen 8B','Llama 8B'],xlim=(0,33),ylim=(-.52,2.52),xticks=[]);bar.tick_params(axis='both',labelsize=6,length=0,pad=2)
        fig.legend(handles=[bar_key(bar_orange,'Joint only'),bar_key(bar_gray,'Single arm also correct')],loc='lower center',bbox_to_anchor=(.53,.006),ncol=2,frameon=False,fontsize=5.9,handlelength=1.2,columnspacing=.8)
        save_figure(fig,'data_main_joint_case_revision')
# END CORETRACE_STORY_POLISH


_final_renderer = make_story_polish


def make_story_polish():
    """Write final manuscript figures without altering the selected PNG artwork."""
    global save_figure
    previous = save_figure
    save_figure = _base_save_figure
    try:
        return _final_renderer()
    finally:
        save_figure = previous


_base_story_revision = make_story_revision


def make_story_revision():
    _base_story_revision()
    make_story_polish()


# Publication rendering lives in this existing entry point.  The measured CSVs
# remain the source of truth; panels and their LaTeX assembly are presentation
# artifacts, never a second analysis pipeline.
_PUB_LAYOUTS = {}
_PUB_FILES = []
_PUB_STYLE = {
    "font.family": "serif",
    # A real TrueType Times-compatible face avoids declaring CFF OpenType
    # outlines as TrueType in Matplotlib's type-42 PDF embedding.
    "font.serif": ["Liberation Serif", "Times New Roman"],
    "mathtext.fontset": "stix",
    "font.size": 8.0, "axes.labelsize": 8.0, "axes.titlesize": 8.0,
    "xtick.labelsize": 7.2, "ytick.labelsize": 7.2,
    "legend.fontsize": 7.6, "axes.linewidth": .55,
    "lines.linewidth": 1.15, "lines.markersize": 3.5,
    "legend.frameon": False, "legend.borderaxespad": .15,
    "legend.borderpad": .1, "legend.handlelength": 1.3,
    "legend.handletextpad": .4, "legend.columnspacing": .9,
    "legend.labelspacing": .25, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.facecolor": "white", "figure.facecolor": "white",
}
_PUB_MODEL_SHORT = ["Qwen3-4B", "Qwen3-8B", "Llama-3.1-8B"]
_PUB_MODEL_TICKS = ["Qwen3\n4B", "Qwen3\n8B", "Llama\n8B"]


def _pub_rows(name):
    """Read released figure data without overwriting or rounding it."""
    return _revision_read_rows(name)


def _pub_one(rows, **criteria):
    matches = [r for r in rows if all(r[k] == v for k, v in criteria.items())]
    if len(matches) != 1:
        raise ValueError(f"Expected one publication record: {criteria}; got {len(matches)}")
    return matches[0]


def _pub_save(fig, stem):
    """Save one independent panel at its intended printed size."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for item in fig.findobj(matplotlib.text.Text):
        if not item.get_visible() or not item.get_text():
            continue
        bounds = item.get_window_extent(renderer)
        if np.isfinite(bounds.extents).all() and bounds.width and bounds.height:
            if (bounds.x0 < -.8 or bounds.y0 < -.8
                    or bounds.x1 > fig.bbox.width + .8
                    or bounds.y1 > fig.bbox.height + .8):
                raise ValueError(f"Publication text outside panel {stem}: {item.get_text()}")
    metadata = {"Creator": "CoReTrace analysis/plot_results.py",
                "CreationDate": None, "ModDate": None}
    fig.savefig(FIGURES / f"{stem}.pdf", metadata=metadata)
    fig.savefig(FIGURES / f"{stem}.png", dpi=300)
    plt.close(fig)
    _PUB_FILES.append(stem)


def _pub_layout(stem, rows, legend=None, width=None):
    """Generate actual subfigure environments, never rasterized (a)/(b) labels.

    Each row contains (panel_stem, LaTeX_caption, fraction_of_linewidth).
    A shared legend may be a stem or (stem, fraction_of_linewidth).
    """
    # Do not wrap these environments in an extra TeX group: subcaption's
    # parent-counter state must survive until the enclosing figure caption.
    pieces = ["% Generated by analysis/plot_results.py; edit that file to regenerate.",
              r"\centering"]
    if legend:
        name, fraction = (legend, 1.0) if isinstance(legend, str) else legend
        pieces += [rf"\includegraphics[width={fraction:.4f}\linewidth]{{figures/{name}.pdf}}",
                   r"\par\vspace{1pt}"]
    for index, row in enumerate(rows):
        if index:
            pieces.append(r"\par\vspace{3pt}")
        for j, (panel, caption, fraction) in enumerate(row):
            if j:
                pieces.append(r"\hfill%")
            pieces += [rf"\begin{{subfigure}}[t]{{{fraction:.4f}\linewidth}}",
                       r"\centering",
                       rf"\includegraphics[width=\linewidth]{{figures/{panel}.pdf}}",
                       rf"\caption{{{caption}}}",
                       rf"\label{{fig:{panel.replace('_', '-')}}}",
                       r"\end{subfigure}%"]
        pieces.append(r"\par")
    (FIGURES / f"{stem}_panels.tex").write_text("\n".join(pieces) + "\n")
    _PUB_LAYOUTS[stem] = {"rows": rows, "legend": legend, "width": width}


def _pub_axes(width, height, *, left=.43, right=.09, bottom=.32, top=.08):
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([left/width, bottom/height,
                       (width-left-right)/width, (height-bottom-top)/height])
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=2.2, width=.55, pad=2)
    ax.grid(axis="y", color="#E1E3E5", linewidth=.45, linestyle=(0, (3, 2)))
    ax.set_axisbelow(True)
    return fig, ax


def _pub_legend(stem, handles, labels, width, *, ncol=None, height=.22, fontsize=7.6):
    fig = plt.figure(figsize=(width, height))
    fig.legend(handles, labels, loc="center", ncol=ncol or len(labels),
               fontsize=fontsize, frameon=False, borderaxespad=0,
               handlelength=1.35, handletextpad=.4, columnspacing=.9,
               labelspacing=.3)
    _pub_save(fig, stem)
    return stem


def _pub_key(color, label=None):
    return Rectangle((0, 0), 1, 1, fc=color, ec=INK, lw=.5, label=label)


def _pub_stack(ax, y, first, total, colors, height=.62):
    assert 0 <= first <= total
    ax.barh(y, total, height, color=colors[0], edgecolor="none", zorder=3)
    ax.barh(y, total-first, height, left=first, color=colors[1], edgecolor="none", zorder=3)
    ax.add_patch(Rectangle((0, y-height/2), total, height, fill=False, ec=INK, lw=.55, zorder=4))
    if 0 < first < total:
        ax.plot([first, first], [y-height/2, y+height/2], color=INK, lw=.55, zorder=4)


def _pub_composition():
    stem = "data_main_composition_address"
    composition = _pub_rows("data_main_composition_address_composition.csv")
    readouts = _pub_rows("data_main_composition_address_readout.csv")
    fig, ax = _pub_axes(3.31, 1.60, left=.87, bottom=.36, top=.30)
    ax.grid(False); ax.grid(axis="x", color=GRID, lw=.45, ls="--")
    ordered = [_pub_one(composition, model=m) for m in MODELS]
    for y, row in zip([2, 1, 0], ordered):
        n, good, bad = [int(row[k]) for k in
                        ("both_constituents_correct", "composition_successes", "composition_failures")]
        assert good + bad == n
        p = 100 * good / n
        _pub_stack(ax, y, p, 100, (BLUE, ORANGE))
        ax.text(p/2, y, f"{good} ({p:.1f}%)", ha="center", va="center",
                fontsize=7.1, color="white", fontweight="bold", zorder=5)
        ax.text((100+p)/2, y, f"{bad} ({100-p:.1f}%)", ha="center", va="center",
                fontsize=7.1, zorder=5)
    ax.set(xlim=(0, 100), ylim=(-.55, 2.55), xticks=[0, 50, 100], yticks=[2, 1, 0],
           yticklabels=[f"{MODEL_NAMES[m]}\n$n={r['both_constituents_correct']}$"
                        for m, r in zip(MODELS, ordered)])
    ax.tick_params(axis="y", length=0, pad=4, labelsize=7.2)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Share of constituent-correct sources (%)", labelpad=3, fontsize=7.8)
    ax.legend([_pub_key(BLUE), _pub_key(ORANGE)], ["Composed correct", "Composed incorrect"],
              loc="lower center", bbox_to_anchor=(.47, 1.025), ncol=2, fontsize=7.4)
    _pub_save(fig, stem+"_a")
    fig, ax = _pub_axes(3.31, 1.60, left=.48, bottom=.43, top=.30)
    xx = np.arange(3)
    for j, (feature, color) in enumerate(zip(("metadata", "attention", "full"),
                                            (LIGHT_GRAY, BLUE, ORANGE))):
        rr = [_pub_one(readouts, model=m, feature_set=feature) for m in MODELS]
        values = np.array([float(r["accuracy_percent"]) for r in rr])
        assert all(np.isclose(v, 100*int(r["correct"])/int(r["n"])) for v, r in zip(values, rr))
        xpos = xx + (j-1)*.23
        ax.bar(xpos, values, .23, color=color, ec=INK, lw=.55, zorder=3)
        if feature == "full":
            for x, v in zip(xpos, values):
                ax.text(x, v+2.0, f"{v:.1f}", ha="center", va="bottom", fontsize=7.5)
    ax.set(ylim=(0, 110), yticks=[0, 50, 100], xticks=xx,
           xticklabels=[f"{s}\n$n={r['composition_failures']}$"
                        for s, r in zip(_PUB_MODEL_TICKS, ordered)])
    ax.tick_params(axis="x", labelsize=7.2, pad=2)
    ax.set_ylabel("Bridge-address accuracy (%)", labelpad=3)
    ax.legend([_pub_key(c) for c in (LIGHT_GRAY, BLUE, ORANGE)], ["Metadata", "Attention", "Full"],
              loc="lower center", bbox_to_anchor=(.5, 1.025), ncol=3, fontsize=7.4)
    _pub_save(fig, stem+"_b")
    _pub_layout(stem, [[(stem+"_a", "Correct hops, failed composition", .49),
                        (stem+"_b", "Bridge addresses in those failures", .49)]], width=6.75)


def _pub_upset(model, stem, *, width=3.31, height=1.55, shared_ylim=30):
    data = _pub_rows("data_main_structure_function_overlap.csv")
    patterns = [(0,0,1), (0,1,0), (0,1,1), (1,0,0), (1,0,1), (1,1,0), (1,1,1)]
    values = [int(_pub_one(data, model=model, selected=str(p[0]),
                           direct=str(p[1]), composed=str(p[2]))["count"]) for p in patterns]
    left = .66 if width > 2.5 else .55
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([left/width, .67/height, (width-left-.05)/width, (height-.74)/height])
    ax.bar(range(7), values, .66, color=[ORANGE if p[0] else LIGHT_GRAY for p in patterns],
           edgecolor=INK, linewidth=.5, zorder=3)
    ax.set(xlim=(-.6, 6.6), ylim=(0, shared_ylim), yticks=[0, 10, 20, 30])
    ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.tick_params(axis="y", length=2, pad=2)
    ax.set_ylabel("Heads", labelpad=3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, ls="--", lw=.4); ax.set_axisbelow(True)
    for x, v in enumerate(values):
        ax.text(x, v+.4, str(v), ha="center", va="bottom", fontsize=7.2)
    matrix = fig.add_axes([left/width, .075/height, (width-left-.05)/width, .48/height])
    for x, p in enumerate(patterns):
        matrix.scatter([x]*3, [2,1,0], s=12, color="#E0E2E5", zorder=2)
        active = [2-i for i, v in enumerate(p) if v]
        color = ORANGE if p[0] else "#58616A"
        matrix.plot([x]*len(active), active, color=color, lw=1.0, zorder=3)
        matrix.scatter([x]*len(active), active, s=15, color=color, zorder=4)
    matrix.set(xlim=(-.6,6.6), ylim=(-.45,2.45), xticks=[], yticks=[2,1,0],
               yticklabels=["Selected","Direct","Composed"])
    matrix.tick_params(length=0, pad=3, labelsize=7.4)
    matrix.spines[:].set_visible(False)
    _pub_save(fig, stem)


def _pub_structure():
    stem = "data_main_structure_function"
    _pub_upset(MODELS[0], stem+"_a", height=1.55)
    profiles = _pub_rows("data_main_structure_function_profiles.csv")
    fig, ax = _pub_axes(3.31, 1.55, left=.81, bottom=.34, top=.36)
    for yi, m in zip([2,1,0], MODELS):
        for shift, key, color in ((.14,"selected",BLUE),(-.14,"random_layer_matched",GRAY)):
            p = [float(_pub_one(profiles, model=m, head_set=key, query=q)["bridge_minus_root_pp"])
                 for q in ("composed","direct_target")]
            ax.plot(p, [yi+shift]*2, color=color, lw=1.25)
            ax.scatter([p[0]],[yi+shift], s=19, fc="white", ec=color, lw=.9, zorder=3)
            ax.scatter([p[1]],[yi+shift], s=19, fc=color, ec=color, lw=.9, zorder=3)
    ax.set(xlim=(-25,31), ylim=(-.45,2.45), xticks=[-20,0,20],
           yticks=[2,1,0], yticklabels=_PUB_MODEL_SHORT)
    ax.grid(False); ax.grid(axis="x", color=GRID, ls="--", lw=.45)
    ax.axvline(0, color="#7D858D", lw=.6)
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Bridge − root mass (pp)", labelpad=3)
    handles = [Line2D([],[],color=BLUE,lw=1.5), Line2D([],[],color=GRAY,lw=1.5),
               Line2D([],[],color=INK,marker="o",mfc="white",ls="none",ms=3.5),
               Line2D([],[],color=INK,marker="o",ls="none",ms=3.5)]
    ax.legend(handles, ["Selected","Matched random","Composed","Direct"],
              ncol=2, loc="lower center", bbox_to_anchor=(.46,1.015), fontsize=7.2)
    _pub_save(fig, stem+"_b")
    headrows = _pub_rows("data_main_structure_function_heads.csv")
    examples = _pub_rows("data_main_structure_function_examples.csv")
    for model, letter in ((MODELS[0],"c"), (MODELS[2],"d")):
        rows = [r for r in headrows if r["model"] == model]
        source_rows = {q: sorted([r for r in rows if r["query"]==q],
                                key=lambda r:int(r["paragraph_index"]))
                       for q in ("composed","direct_target")}
        matrix = np.array([[float(r["attention_mass_percent"]) for r in source_rows[q]]
                           for q in ("composed","direct_target")])
        assert matrix.shape == (2,10)
        fig = plt.figure(figsize=(3.31,1.77))
        ax = fig.add_axes([.54/3.31,.63/1.77,2.64/3.31,.35/1.77])
        image = ax.imshow(matrix, vmin=0, vmax=70, cmap="Blues", aspect="auto", interpolation="nearest")
        ax.set(xticks=range(10), xticklabels=[f"P{i}" for i in range(10)],
               yticks=[0,1], yticklabels=["Composed","Direct"])
        ax.tick_params(length=0,pad=2,labelsize=7.0); ax.spines[:].set_visible(False)
        for idx, r in enumerate(source_rows["composed"]):
            if r["role"] in ("root","bridge"):
                color = ORANGE if r["role"] == "root" else BLUE
                ax.add_patch(Rectangle((idx-.5,-.5),1,2,fill=False,ec=color,lw=1.1))
                for row in range(2):
                    ax.text(idx,row,f"{matrix[row,idx]:.1f}",ha="center",va="center",
                            fontsize=6.7,color="white" if matrix[row,idx] > 38 else INK)
        top = 1.72
        for q, label in (("composed",r"$q_{12}$"),("direct_target",r"$q_2$")):
            question = source_rows[q][0]["question"]
            lines = textwrap.wrap(question, width=66)
            fig.text(.025,top/1.77,label+": "+ "\n".join(lines),ha="left",va="top",
                     fontsize=7.2,linespacing=1.05)
            top -= .135*len(lines)+.045
        cax = fig.add_axes([.65/3.31,1.15/1.77,2.48/3.31,.065/1.77])
        colorbar = fig.colorbar(image,cax=cax,orientation="horizontal",ticks=[0,35,70])
        colorbar.outline.set_visible(False)
        colorbar.ax.tick_params(length=1.2,pad=1,labelsize=6.8)
        fig.text(.025,1.18/1.77,"Mass (%)",va="center",fontsize=7.2)
        root = next(r for r in source_rows["composed"] if r["role"]=="root")
        bridge = next(r for r in source_rows["composed"] if r["role"]=="bridge")
        fig.text(.025,.41/1.77,f"Root P{root['paragraph_index']}: {root['paragraph_title']}",
                 va="center",fontsize=7.3,color="#A85C30")
        fig.text(.025,.26/1.77,f"Bridge P{bridge['paragraph_index']}: {bridge['paragraph_title']}",
                 va="center",fontsize=7.3,color="#315F93")
        native = _pub_one(examples,model=model,condition="native")
        calibrated = _pub_one(examples,model=model,condition="calibrated")
        fig.text(.025,.065/1.77,
                 f"{calibrated['selected_head_count']}-head set: {native['answer']} → {calibrated['answer']}",
                 fontsize=7.4,va="center")
        _pub_save(fig,stem+"_"+letter)
    _pub_layout(stem, [
        [(stem+"_a","Head-set intersections (Qwen3-4B)",.49),
         (stem+"_b","Paired root-to-bridge preference",.49)],
        [(stem+"_c","Qwen3-4B: L23H10",.49),
         (stem+"_d","Llama-3.1-8B: L13H18",.49)]],width=6.75)
    app = "data_app_head_overlap"
    for i,m in enumerate(MODELS):
        _pub_upset(m,app+f"_{chr(97+i)}",width=2.045,height=1.65)
    _pub_layout(app,[[(app+f"_{chr(97+i)}",MODEL_NAMES[m],.326)
                     for i,m in enumerate(MODELS)]],width=6.2775)


def _pub_localization():
    from matplotlib.colors import TwoSlopeNorm
    rows = _pub_rows("data_app_localization.csv")
    membership = _pub_rows("data_app_head_membership.csv")
    profiles = _pub_rows("data_app_localization_layer_profiles.csv")
    limit = .34
    norm = TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit)
    for stem, total_width, panel_width, panel_height in (
            ("data_main_localization", 3.25, 1.0595, 1.27),
            ("data_app_localization", 6.345, 2.0685, 1.94)):
        for j, model in enumerate(MODELS):
            rr = [r for r in rows if r["model"] == model]
            nl = max(int(r["layer"]) for r in rr)+1
            nh = max(int(r["head"]) for r in rr)+1
            matrix = np.full((nl, nh), np.nan)
            selected = []
            for r in rr:
                layer, head = int(r["layer"]), int(r["head"])
                value = float(r["score"])
                assert np.isclose(value, float(r["direct_target_all_question_mean"])
                                  - float(r["composed_all_question_mean"]))
                matrix[layer, head] = value
                if r["selected"] == "True":
                    selected.append((layer, head))
            assert np.isfinite(matrix).all() and len(selected) == (20,20,40)[j]
            overlap = {(int(r["layer"]), int(r["head"])) for r in membership
                       if r["model"] == model and r["ranked"] == "1" and r["direct"] == "1"}
            assert len(overlap) == (14,14,31)[j] and overlap.issubset(set(selected))
            left = .28 if total_width < 4 else .36
            bottom = .27 if total_width < 4 else .32
            fig, ax = _pub_axes(panel_width, panel_height, left=left, right=.035,
                               bottom=bottom, top=.025)
            ax.grid(False)
            ax.imshow(matrix, cmap="RdBu_r", norm=norm, origin="upper",
                      aspect="equal", interpolation="nearest")
            ax.set_anchor("N")
            for layer, head in selected:
                ax.add_patch(Rectangle((head-.48,layer-.48),.96,.96,
                                       fill=False,ec="#363A40",lw=.35 if total_width < 4 else .55))
            if overlap:
                coords = sorted(overlap)
                ax.scatter([h for l,h in coords],[l for l,h in coords],
                           s=.8 if total_width < 4 else 2.2,c="#17191C",zorder=5,linewidths=0)
            ax.set(xticks=[0,16,31], yticks=[0,16,nl-1],
                   xlim=(-.5,nh-.5), ylim=(nl-.5,-.5))
            ax.tick_params(length=1.5,pad=1.4,labelsize=6.8 if total_width < 4 else 7.4)
            ax.set_xlabel("Head",labelpad=1.5,fontsize=7.3 if total_width < 4 else 8)
            if j == 0:
                ax.set_ylabel("Layer",labelpad=2,fontsize=7.3 if total_width < 4 else 8)
            ax.spines[:].set_visible(False)
            _pub_save(fig,stem+f"_{chr(97+j)}")
        key = stem+"_legend"
        fig = plt.figure(figsize=(total_width,.56))
        cax = fig.add_axes([.15,.36,.70,.15])
        mappable = matplotlib.cm.ScalarMappable(norm=norm,cmap="RdBu_r")
        cb = fig.colorbar(mappable,cax=cax,orientation="horizontal",ticks=[-.3,-.15,0,.15,.3])
        cb.outline.set_visible(False); cb.ax.xaxis.set_ticks_position("top")
        cb.ax.tick_params(labelsize=7.0,length=1.5,pad=1)
        fig.text(.5,.94,"Bridge-attention score (direct − composed)",
                 ha="center",va="top",fontsize=7.6)
        fig.legend([Rectangle((0,0),1,1,fill=False,ec="#363A40",lw=.6),
                    Line2D([],[],color="#17191C",marker="o",ls="none",ms=2.8)],
                   ["Selected",r"Selected $\cap$ direct top-$k$"],loc="lower center",
                   bbox_to_anchor=(.5,-.02),ncol=2,fontsize=7.2,
                   handlelength=.9,handletextpad=.4,columnspacing=1.1)
        _pub_save(fig,key)
        layout = [[(stem+f"_{chr(97+j)}",MODEL_NAMES[m],.326) for j,m in enumerate(MODELS)]]
        if stem == "data_app_localization":
            for j,model in enumerate(MODELS):
                pp = sorted([r for r in profiles if r["model"]==model],key=lambda r:int(r["layer"]))
                fig,ax = _pub_axes(panel_width,1.30,left=.38,right=.05,bottom=.32,top=.05)
                for field,color,label in (("mean_score",BLUE,"Mean"),("maximum_score",ORANGE,"Maximum")):
                    ax.plot([int(r["layer"]) for r in pp],[float(r[field]) for r in pp],
                            color=color,lw=1.15,label=label)
                ax.set(xlim=(0,len(pp)-1),ylim=(-.015,.35),xticks=[0,16,len(pp)-1],
                       yticks=[0,.15,.30])
                ax.set_xlabel("Layer",labelpad=2)
                if j == 0: ax.set_ylabel("Score",labelpad=2)
                ax.legend(loc="upper left",ncol=1,fontsize=7.3)
                _pub_save(fig,stem+f"_{chr(100+j)}")
            layout.append([(stem+f"_{chr(100+j)}",f"{MODEL_NAMES[m]}: layer profile",.326)
                           for j,m in enumerate(MODELS)])
        _pub_layout(stem,layout,legend=key,width=total_width)


def _pub_knockout():
    rows = _pub_rows("data_app_necessity.csv")
    values = {(r["model"],r["query"],r["selection"],int(r["knocked_out"])):
              float(r["accuracy_percent"]) for r in rows}
    assert len(values) == 63 and all(int(r["n"])==1000 for r in rows)
    styles, markers = ["-","--",":"], ["o","s","^"]
    for stem, queries, labels, width, total_width, delta in (
            ("data_main_head_causality",["composed","direct_target"],
             ["Composed","Direct second hop"],1.5925,3.25,False),
            ("data_app_necessity",["composed","direct_first","direct_target"],
             ["Composed","First hop","Second hop"],2.2005,6.75,True)):
        for j,query in enumerate(queries):
            fig,ax = _pub_axes(width,1.24 if not delta else 1.58,
                               left=.34 if not delta else .45,bottom=.32,top=.06)
            for i,m in enumerate(MODELS):
                baseline = values[m,query,"native",0]
                for group,color in (("selected",ORANGE),("random",GRAY)):
                    vals = np.array([baseline]+[values[m,query,group,d] for d in (20,40,80)])
                    if delta: vals -= baseline
                    ax.plot([0,20,40,80],vals,color=color,ls=styles[i],marker=markers[i],
                            ms=3.1,mfc=color if group=="selected" else "white",mew=.65,lw=1.05)
            ax.set_xticks([0,20,40,80])
            ax.set_xlim(-3,83)
            if delta:
                minimum = min(values[m,query,group,d]-values[m,query,"native",0]
                              for m in MODELS for group in ("selected","random") for d in (20,40,80))
                lower = 5*np.floor((minimum-2)/5)
                step = 20 if lower < -40 else 10
                ax.set_ylim(lower,4)
                ax.set_yticks(np.arange(step*np.ceil(lower/step),1,step))
                ax.axhline(0,color=INK,lw=.55)
                ax.set_ylabel("EM change (pp)",labelpad=2)
            else:
                ax.set_ylim((0,40) if query=="composed" else (0,65))
                ax.set_yticks([0,20,40] if query=="composed" else [0,20,40,60])
                if j==0: ax.set_ylabel("EM (%)",labelpad=2,fontsize=7.6)
            ax.set_xlabel("Heads removed",labelpad=2,fontsize=7.6)
            _pub_save(fig,stem+f"_{chr(97+j)}")
        handles = [Line2D([],[],color=ORANGE,lw=1.4),Line2D([],[],color=GRAY,lw=1.4)]
        handles += [Line2D([],[],color=INK,marker=mk,ls=ls,ms=3.1) for mk,ls in zip(markers,styles)]
        names = ["Ranked","Layer-matched random","Qwen3-4B","Qwen3-8B","Llama-3.1-8B"]
        if delta:
            key = _pub_legend(stem+"_legend",handles,names,total_width,ncol=5,height=.23)
        else:
            # Separate rows keep treatment and model encodings easy to read.
            fig = plt.figure(figsize=(total_width,.37))
            fig.legend(handles[:2],names[:2],loc="center",bbox_to_anchor=(.5,.76),ncol=2,fontsize=7.3)
            fig.legend(handles[2:],names[2:],loc="center",bbox_to_anchor=(.5,.25),ncol=3,
                       fontsize=7.1,handlelength=1.6,columnspacing=.8)
            key = stem+"_legend"; _pub_save(fig,key)
        fraction = .49 if len(queries)==2 else .326
        _pub_layout(stem,[[(stem+f"_{chr(97+j)}",label,fraction) for j,label in enumerate(labels)]],
                    legend=key,width=total_width)


def _pub_routing():
    stem = "data_main_address_routing"
    allrows = _pub_rows("data_main_address_routing_all_sources.csv")
    massrows = _pub_rows("data_main_address_routing_mass.csv")
    condrows = _pub_rows("data_main_address_routing_conditional.csv")
    denominators = []
    for model in MODELS:
        n = int(_pub_one(massrows, model=model, role="bridge")["n"])
        assert int(_pub_one(massrows, model=model, role="root")["n"]) == n
        assert all(int(r["n"]) == n for r in condrows if r["model"] == model)
        denominators.append(n)
    methods = ["oracle_second_paragraph","oracle_first_paragraph","lengthmatched_other_paragraph"]
    colors = [BLUE,ORANGE,GRAY]
    for j in range(3):
        fig,ax = _pub_axes(2.2005,1.48,left=.43,bottom=.40,top=.07)
        xx = np.arange(3)
        if j in (0,2):
            rows = allrows if j==0 else condrows
            field,lo,hi = (("delta_pp","CI95_low_pp","CI95_high_pp") if j==0 else
                           ("repair_percent","CI95_low_percent","CI95_high_percent"))
            for k,(method,color) in enumerate(zip(methods,colors)):
                rr = [_pub_one(rows,model=m,method=method) for m in MODELS]
                vals = np.array([float(r[field]) for r in rr])
                low, high = [np.array([float(r[f]) for r in rr]) for f in (lo,hi)]
                pos = xx+(k-1)*.24
                ax.bar(pos,vals,.215,color=color,ec=INK,lw=.5,yerr=[vals-low,high-vals],
                       error_kw={"elinewidth":.65,"capsize":1.6,"capthick":.65},zorder=3)
                if j==2:
                    for x,v,r,h in zip(pos,vals,rr,high):
                        ax.text(x,h+1.3,r["corrected"],ha="center",va="bottom",fontsize=7.1)
            if j==0:
                ax.set(ylim=(-27,24),yticks=[-20,0,20],ylabel="EM change (pp)")
                ax.axhline(0,color=INK,lw=.6)
            else:
                ax.set(ylim=(0,67),yticks=[0,20,40,60],ylabel="Repaired (%)")
        else:
            for k,(role,color) in enumerate(zip(("root","bridge"),(ORANGE,BLUE))):
                vals = [float(_pub_one(massrows,model=m,role=role)["attention_mass_percent"]) for m in MODELS]
                pos = xx+(k-.5)*.30
                ax.bar(pos,vals,.27,color=color,ec=INK,lw=.5,zorder=3)
                for x,v in zip(pos,vals):
                    ax.text(x,v+.8,f"{v:.1f}",ha="center",va="bottom",fontsize=7.1)
            ax.set(ylim=(0,40),yticks=[0,20,40],ylabel="Attention mass (%)")
        ax.set_xticks(xx, _PUB_MODEL_TICKS if j==0 else
                      [f"{s}\n$n={n}$" for s,n in zip(_PUB_MODEL_TICKS,denominators)])
        ax.tick_params(axis="x",labelsize=7.0,pad=2)
        ax.yaxis.labelpad=2
        _pub_save(fig,stem+f"_{chr(97+j)}")
    key = _pub_legend(stem+"_legend",[_pub_key(c) for c in colors],["Bridge","Root","Other"],6.75)
    _pub_layout(stem,[[(stem+"_a","Destination controls",.326),
                       (stem+"_b","Native allocation",.326),
                       (stem+"_c","Routing repair",.326)]],legend=key,width=6.75)


def _pub_relation_tokens():
    from matplotlib.colors import LinearSegmentedColormap
    data = read_json("analysis/figure_data/data_revision_token_capture.json")
    assert data["status"]=="MEASURED_READONLY_CAPTURE" and data["head_count"]==40
    spans = [[26],[76,77],[89,90,91,92]]
    assert data["span_indices"]["Inge Morath"]==spans[2]
    states = ["native_composed","native_direct_same_relation","native_direct_other_relation","adapted_composed"]
    records = {r["state"]:r for r in data["states"]}
    values = 100*np.array([[sum(records[s]["conditional_mean"][i] for i in ids)
                           for ids in spans] for s in states])
    assert np.isfinite(values).all() and (values>=0).all()
    fig=plt.figure(figsize=(3.25,1.53))
    ax=fig.add_axes([1.06/3.25,.40/1.53,2.12/3.25,.86/1.53])
    cmap=LinearSegmentedColormap.from_list("coretrace_read",["#FAFBFC","#BED3E6","#32699B"])
    maximum=max(30,values.max())
    ax.imshow(values,cmap=cmap,vmin=0,vmax=maximum,aspect="auto",interpolation="nearest")
    for i in range(4):
        for j in range(3):
            ax.text(j,i,f"{values[i,j]:.1f}",ha="center",va="center",fontsize=8.5,
                    color="white" if values[i,j]>.60*maximum else INK)
    ax.set_xticks(range(3),["American\n(nationality)","Arthur Miller\n(father)","Inge Morath\n(mother)"])
    ax.set_yticks(range(4),["Native composed","Direct mother","Direct nationality","Adapted + restored"])
    ax.tick_params(length=0,pad=3,labelsize=7.4);ax.spines[:].set_visible(False)
    ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,4,1),minor=True)
    ax.grid(which="minor",color="white",lw=1.2);ax.tick_params(which="minor",length=0)
    ax.add_patch(Rectangle((1.51,-.49),.98,3.98,fill=False,ec=GREEN,lw=.9))
    fig.text(.65,.965,"Conditional span weight (%)",ha="center",va="top",fontsize=8)
    _pub_save(fig,"data_main_relation_tokens_final")


def _pub_interaction():
    factors = _pub_rows("data_fig4_causal_factorial.csv")
    contrasts = _pub_rows("data_fig4_causal_factorial_contrasts.csv")
    stem = "data_main_interaction_revision"
    captions = []
    for i,m in enumerate(MODELS):
        vv = {k:float(_pub_one(factors,model=m,method=k)["accuracy_percent"])
              for k in ("native","conditional_only","mass_only","both")}
        ci = _pub_one(contrasts,model=m,contrast="interaction")
        est,lo,hi = [float(ci[k]) for k in ("estimate_pp","CI95_low_pp","CI95_high_pp")]
        assert np.isclose(vv["both"]-vv["mass_only"]-vv["conditional_only"]+vv["native"],est)
        fig,ax = _pub_axes(2.2005,1.18,left=.41,right=.09,bottom=.30,top=.08)
        for keys,color,dy in ((("native","conditional_only"),GRAY,-8),(("mass_only","both"),ORANGE,5)):
            vals = [vv[k] for k in keys]
            ax.plot([0,1],vals,marker="o",ms=3.8,color=color,lw=1.3)
            for x,v in enumerate(vals):
                ax.annotate(f"{v:.0f}",(x,v),xytext=(0,dy),textcoords="offset points",
                            ha="center",fontsize=7.5,color=INK)
            ax.annotate(f"{vals[1]-vals[0]:+.0f} pp",(.5,sum(vals)/2),xytext=(0,dy),
                        textcoords="offset points",ha="center",fontsize=7.3,color=color)
        ax.set(xlim=(-.17,1.17),ylim=(10,96),yticks=[20,40,60,80])
        ax.set_xticks([0,1],[r"Native $\rho$",r"Direct $\rho^{\rm dir}$"])
        if i==0:ax.set_ylabel("Composed EM (%)",labelpad=2)
        _pub_save(fig,stem+f"_{chr(97+i)}")
        captions.append(f"{MODEL_NAMES[m]}: $I={est:+.0f}$ pp $[{lo:.0f}, {hi:.0f}]$")
    key = _pub_legend(stem+"_legend",
        [Line2D([],[],color=GRAY,marker="o",ms=3.5),Line2D([],[],color=ORANGE,marker="o",ms=3.5)],
        [r"Native access $m$",r"Calibrated access $\tau$"],6.75)
    _pub_layout(stem,[[(stem+f"_{chr(97+i)}",captions[i],.326) for i in range(3)]],
                legend=key,width=6.75)


def _pub_dumbbell(stem, starts, ends, *, width, height=1.35, color=BLUE,
                  xlabel="Accuracy (%)", limits=(0,105), ticks=(0,50,100),
                  model_labels=True, values=True, deltas=False):
    fig,ax = _pub_axes(width,height,left=.83 if model_labels else .18,
                       right=.14,bottom=.34,top=.18)
    for yi,v0,v1 in zip([2,1,0],starts,ends):
        ax.plot([v0,v1],[yi,yi],color=color,lw=1.5,zorder=2)
        ax.scatter([v0],[yi],s=20,color=GRAY,zorder=3)
        ax.scatter([v1],[yi],s=24,color=color,zorder=3)
        if values:
            ax.annotate(f"{v0:.1f}",(v0,yi),xytext=(-3,5),textcoords="offset points",
                        ha="right",fontsize=7.2,color="#555B63")
            ax.annotate(f"{v1:.1f}",(v1,yi),xytext=(3,5),textcoords="offset points",
                        ha="left",fontsize=7.2,color=color)
        if deltas:
            ax.annotate(f"{v1-v0:+.1f}",((v0+v1)/2,yi),xytext=(0,5),textcoords="offset points",
                        ha="center",fontsize=7.5,color=color)
    ax.set(xlim=limits,ylim=(-.42,2.53),xticks=ticks,yticks=[2,1,0])
    ax.set_yticklabels(_PUB_MODEL_SHORT if model_labels else ["","",""])
    ax.tick_params(axis="y",length=0,pad=4,labelsize=7.4)
    ax.spines[["top","right","left"]].set_visible(False)
    ax.grid(False);ax.grid(axis="x",color=GRID,lw=.45,ls="--");ax.set_axisbelow(True)
    ax.set_xlabel(xlabel,labelpad=3,fontsize=7.7)
    _pub_save(fig,stem)


def _pub_closure_and_selection():
    addresses = _pub_rows("data_revision_mechanism_repair.csv")
    routing = _pub_rows("data_revision_adapted_routing.csv")
    reading = _pub_rows("data_revision_relation_reading_summary.csv")
    stem = "data_main_mechanism_closure_final"
    for j,color in enumerate((BLUE,ORANGE,GREEN)):
        before,after = [],[]
        for m,n in zip(MODELS,(234,236,243)):
            if j==0:
                r=_pub_one(addresses,model=m)
                keys=("native_attention_failure_address","adapted_attention_failure_address")
            elif j==1:
                r=_pub_one(routing,model=m,population="fixed_native_failures",target="bridge")
                assert int(r["n"])==n
                keys=("native_mass_percent","adapted_mass_percent")
            else:
                r=_pub_one(reading,model=m,metric="conditional_margin",contrast="adapted_vs_native")
                assert int(r["n_receivers"])==98 and int(r["n_clusters"])==25
                keys=("native_composed","adapted_composed")
            before.append(float(r[keys[0]]));after.append(float(r[keys[1]]))
        panel_width = 2.5238 if j==0 else 1.8738
        _pub_dumbbell(stem+f"_{chr(97+j)}",before,after,width=panel_width,height=1.35,color=color,
                      xlabel=("Readout accuracy (%)","Bridge mass (%)","Target − other (pp)")[j],
                      limits=((52,105),(0,20),(-3,36))[j],
                      ticks=([60,80,100],[0,10,20],[0,15,30])[j],model_labels=(j==0))
    key=_pub_legend(stem+"_legend",
                    [Line2D([],[],color=GRAY,marker="o",ls="none",ms=4),
                     Line2D([],[],color=INK,marker="o",ls="none",ms=4)],
                    ["Native",r"Adapted + restored $\mathcal{M}^{*}$ (colored)"],6.4125)
    _pub_layout(stem,[[(stem+"_a","Locate: address",.393576),
                       (stem+"_b",r"Route: bridge $m$",.292212),
                       (stem+"_c",r"Read: conditional $\rho$",.292212)]],legend=key,width=6.4125)
    stem="data_main_address_signal_final"
    for j,(ka,kb) in enumerate((("ambiguous_input_order_address","ambiguous_full_reader_address"),
                                ("ambiguous_input_order_em","ambiguous_full_reader_em"))):
        rr=[_pub_one(addresses,model=m) for m in MODELS]
        _pub_dumbbell(stem+f"_{chr(97+j)}",
                      [float(r[ka]) for r in rr],[float(r[kb]) for r in rr],
                      width=1.9175 if j==0 else 1.2675,height=1.22,limits=(25,101),ticks=[30,60,90],
                      model_labels=(j==0),values=False)
    key=_pub_legend(stem+"_legend",
                    [Line2D([],[],color=GRAY,marker="o",ls="none",ms=4),
                     Line2D([],[],color=BLUE,marker="o",ls="none",ms=4)],
                    ["Input order","Address reader"],3.25)
    _pub_layout(stem,[[(stem+"_a","Bridge choice",.59),(stem+"_b","Composed EM",.39)]],
                legend=key,width=3.25)
    # The appendix repeats the identical ambiguous-input population at a larger
    # physical size, with grouped bars and the same color semantics.
    stem="data_main_ambiguity"
    for j,(ka,kb) in enumerate((("ambiguous_input_order_address","ambiguous_full_reader_address"),
                                ("ambiguous_input_order_em","ambiguous_full_reader_em"))):
        fig,ax=_pub_axes(2.31525,1.55,left=.43,bottom=.36,top=.06)
        for k,(key,color) in enumerate(((ka,GRAY),(kb,BLUE))):
            vv=[float(_pub_one(addresses,model=m)[key]) for m in MODELS]
            pos=np.arange(3)+(k-.5)*.32
            ax.bar(pos,vv,.29,color=color,ec=INK,lw=.5,zorder=3)
            for x,v in zip(pos,vv):
                ax.text(x,v+1.5,f"{v:.1f}",ha="center",va="bottom",fontsize=7.0)
        ax.set(ylim=(0,110),yticks=[0,50,100],xticks=range(3),xticklabels=_PUB_MODEL_TICKS,
               ylabel="Accuracy (%)")
        _pub_save(fig,stem+f"_{chr(97+j)}")
    key=_pub_legend(stem+"_legend",[_pub_key(GRAY),_pub_key(BLUE)],
                    ["Input order","Full reader"],4.725)
    _pub_layout(stem,[[(stem+"_a","Bridge address",.49),(stem+"_b","Composed EM",.49)]],
                legend=key,width=4.725)


def _pub_appendix_bars():
    ablation=_pub_rows("data_app_ablation_aggregated.csv")
    capabilities=_pub_rows("data_app_capabilities_aggregated.csv")
    for stem,data,fields,field_name,labels,method_sets,colors,legend_labels in (
        ("data_app_ablation",ablation,["direct_first","all3","gsm8k"],"query",
         ["First hop","All three","GSM8K"],
         [["head_tuning","scoped_body"],["head_tuning","scoped_body"],["head_tuning","final"]],
         [ORANGE,GREEN],["Head tuning","+ native-projection restoration"]),
        ("data_app_capabilities",capabilities,["hotpot","mmlu","gsm8k"],"dataset",
         ["HotpotQA","MMLU","GSM8K"],[["native","fullft","final"]]*3,
         [GRAY,ORANGE,GREEN],["Native","Full fine-tuning","CoReTrace"])):
        for j,(field,methods) in enumerate(zip(fields,method_sets)):
            fig,ax=_pub_axes(2.2005,1.58,left=.41,right=.04,bottom=.38,top=.07)
            barw=.24 if len(methods)==3 else .32
            for k,(method,color) in enumerate(zip(methods,colors)):
                rr=[_pub_one(data,model=m,**{field_name:field,"method":method}) for m in MODELS]
                vals=np.array([float(r["mean_percent"]) for r in rr])
                err=np.array([float(r["sample_sd_percent"]) for r in rr])
                xpos=np.arange(3)+(k-(len(methods)-1)/2)*barw
                ax.bar(xpos,vals,.90*barw,color=color,ec=INK,lw=.5,yerr=err,
                       error_kw={"elinewidth":.6,"capsize":1.5,"capthick":.6},zorder=3)
                # Preserve zero measurements as visible baselines rather than
                # replacing them with a small fabricated bar.
                for x,v in zip(xpos,vals):
                    if v==0:
                        ax.text(x,1.2,"0",ha="center",va="bottom",fontsize=7.1)
            ax.set(ylim=(0,103),yticks=[0,25,50,75,100],xticks=range(3),
                   xticklabels=_PUB_MODEL_TICKS)
            if j==0:ax.set_ylabel("Accuracy (%)",labelpad=3)
            _pub_save(fig,stem+f"_{chr(97+j)}")
        key=_pub_legend(stem+"_legend",[_pub_key(c) for c in colors],legend_labels,6.75)
        _pub_layout(stem,[[(stem+f"_{chr(97+j)}",label,.326) for j,label in enumerate(labels)]],
                    legend=key,width=6.75)
    stem="data_main_restoration_revision"
    for j,q in enumerate(("direct_first","all3")):
        start=[float(_pub_one(ablation,model=m,query=q,method="head_tuning")["mean_percent"]) for m in MODELS]
        end=[float(_pub_one(ablation,model=m,query=q,method="scoped_body")["mean_percent"]) for m in MODELS]
        _pub_dumbbell(stem+f"_{chr(97+j)}",start,end,width=1.9845,height=1.45,
                      color=GREEN,limits=(20,80),ticks=[20,40,60,80],
                      model_labels=(j==0),values=False,deltas=True)
    key=_pub_legend(stem+"_legend",
                    [Line2D([],[],color=GRAY,marker="o",ls="none",ms=4),
                     Line2D([],[],color=GREEN,marker="o",ls="none",ms=4)],
                    ["Head tuning","+ native-projection restoration"],4.05)
    _pub_layout(stem,[[(stem+"_a","First hop",.49),(stem+"_b","All three",.49)]],
                legend=key,width=4.05)
    data=_pub_rows("data_revision_mechanism_repair.csv")
    stem="data_main_repair_chain_revision"
    definitions=[
        ("native_attention_failure_address","adapted_attention_failure_address","Internal address signal",
         ("Native","Adapted + restored")),
        ("ambiguous_input_order_address","ambiguous_full_reader_address","Ambiguous bridge choice",
         ("Input order","Full reader")),
        ("ambiguous_input_order_em","ambiguous_full_reader_em","Composed answers",
         ("Input order","Full reader"))]
    for j,(ka,kb,label,legend_labels) in enumerate(definitions):
        fig,ax=_pub_axes(2.0685,1.69,left=.40,right=.04,bottom=.38,top=.35)
        for k,(key,color) in enumerate(((ka,GRAY),(kb,BLUE))):
            vals=[float(_pub_one(data,model=m)[key]) for m in MODELS]
            pos=np.arange(3)+(k-.5)*.32
            ax.bar(pos,vals,.29,color=color,ec=INK,lw=.5,zorder=3)
            for x,v in zip(pos,vals):
                ax.text(x,v+1.2,f"{v:.1f}",ha="center",va="bottom",fontsize=6.9)
        ax.set(ylim=(0,110),yticks=[0,50,100],xticks=range(3),xticklabels=_PUB_MODEL_TICKS)
        if j==0:ax.set_ylabel("Accuracy (%)",labelpad=2)
        ax.legend([_pub_key(GRAY),_pub_key(BLUE)],legend_labels,
                  loc="lower center",bbox_to_anchor=(.5,1.015),ncol=1 if j==0 else 2,fontsize=7.3)
        _pub_save(fig,stem+f"_{chr(97+j)}")
    _pub_layout(stem,[[(stem+f"_{chr(97+j)}",definition[2],.326)
                      for j,definition in enumerate(definitions)]],width=6.345)


def _pub_conceptual_panels():
    """Use exact PDF viewports of the supplied artwork, with TeX captions.

    Only the old title bands and gutters are excluded.  The original concept
    PNG/PDF assets remain unmodified, and all diagrams retain their exact content.
    """
    # Coordinates below are fractions of the source image, origin at top left.
    definitions={
        "figure1_teaser_revision": (
            3.25,
            [[("a",(.006,.083,.998,.282),"Correct hops, failed composition",1.0)],
             [("b",(.006,.382,.998,.780),"Locating evidence is not enough",1.0)],
             [("c",(.006,.870,.998,.994),"CoReTrace coordinates evidence use",1.0)]]),
        "figure2_diagnosis_revision": (
            6.75,
            [[("a",(.006,.077,.994,.413),"Paired-query localization",1.0)],
             [("b",(.006,.516,.481,.980),"Locate, Route and Read",.484),
              ("c",(.495,.516,.993,.980),"Factorized causal interventions",.507)]]),
        "figure3_method_revision": (
            6.75,
            [[("a",(.008,.072,.994,.351),"Offline preparation",1.0)],
             [("b",(.008,.449,.994,.982),"Inference",1.0)]]),
    }
    import fitz
    for stem,(width,rows) in definitions.items():
        source_pdf=FIGURES/f"{stem}.pdf"
        source_png=FIGURES/f"{stem}.png"
        INPUT_PATHS.add(source_png.relative_to(ROOT).as_posix())
        # Source PNG is the immutable author artwork; reconstructing a temporary
        # PDF prevents a previous compiled overview from becoming the source.
        pixels=plt.imread(source_png)
        h,w=pixels.shape[:2]
        source=fitz.open()
        page=source.new_page(width=w,height=h)
        page.insert_image(page.rect,filename=str(source_png))
        newrows=[]
        for row in rows:
            newrow=[]
            for letter,(x0,y0,x1,y1),caption,fraction in row:
                target=stem+"_"+letter
                clip=fitz.Rect(x0*w,y0*h,x1*w,y1*h)
                target_width=width*fraction*72
                target_height=target_width*clip.height/clip.width
                panel=fitz.open()
                out=panel.new_page(width=target_width,height=target_height)
                out.show_pdf_page(out.rect,source,0,clip=clip)
                panel.save(FIGURES/f"{target}.pdf",garbage=3,deflate=True,no_new_id=True)
                pix=out.get_pixmap(matrix=fitz.Matrix(300/72,300/72),alpha=False)
                pix.save(FIGURES/f"{target}.png")
                panel.close()
                _PUB_FILES.append(target)
                newrow.append((target,caption,fraction))
            newrows.append(newrow)
        source.close()
        _pub_layout(stem,newrows,width=width)


def _pub_compile_overviews():
    """Typeset standalone previews with the same real LaTeX subcaptions."""
    import os
    import shutil
    import fitz
    if not shutil.which("pdflatex"):
        raise RuntimeError("Publication previews require pdfLaTeX; run the paper build in a TeX environment.")
    build=ROOT/"analysis"/"build_figure_previews"
    build.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    runtime=ROOT/"analysis"/"tex_runtime"
    if (runtime/"web2c"/"pdflatex.fmt").exists():
        dist=subprocess.check_output(["kpsewhich","--var-value=TEXMFDIST"],text=True).strip()
        env.update({"TEXMF":"{"+str(runtime)+","+dist+"}",
                    "TEXMFVAR":str(runtime),"TEXMFCONFIG":str(runtime/"config"),
                    "TEXMFHOME":str(runtime/"home"),"TEXFORMATS":str(runtime/"web2c")+"//:",
                    "VARTEXFONTS":str(runtime/"fonts")})
    template=r"""
\documentclass{article}
\usepackage[T1]{fontenc}
\usepackage{graphicx,subcaption,times,amsmath,amssymb,xcolor}
\captionsetup{hypcap=false}
\DeclareCaptionFont{panelfont}{\normalfont\fontsize{9}{10.5}\selectfont}
\captionsetup[subfigure]{font=panelfont,labelfont=normalfont,textfont=normalfont,
labelformat=parens,labelsep=space,justification=centering,singlelinecheck=false,skip=3pt,margin=0pt}
\pagestyle{empty}
\newsavebox{\panelpreview}
\begin{document}
\begin{lrbox}{\panelpreview}%
\begin{minipage}{WIDTHin}
\captionsetup{type=figure}\centering
\input{figures/STEM_panels.tex}
\end{minipage}%
\end{lrbox}
\pdfpagewidth=\wd\panelpreview
\pdfpageheight=\dimexpr\ht\panelpreview+\dp\panelpreview\relax
\pdfhorigin=0pt \pdfvorigin=0pt
\shipout\vbox{\offinterlineskip\box\panelpreview}
\end{document}
"""
    for stem,spec in _PUB_LAYOUTS.items():
        width=spec["width"] or (6.75 if stem=="data_main_mechanism_cases" else 3.25)
        tex=build/f"{stem}.tex"
        tex.write_text(template.replace("WIDTH",f"{width:.5f}").replace("STEM",stem))
        with (build/f"{stem}_stdout.txt").open("w") as log:
            result=subprocess.run(["pdflatex","-interaction=nonstopmode","-halt-on-error",
                                   "-file-line-error","-output-directory="+str(build),str(tex)],
                                  cwd=ROOT/"paper",env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f"Standalone LaTeX figure failed: {stem}; see {build}/{stem}_stdout.txt")
        # Author-selected PNGs remain immutable inputs.  Numerical group previews
        # keep the historical filenames, but the manuscript imports their panels.
        if not stem.startswith("figure"):
            shutil.copy2(build/f"{stem}.pdf",FIGURES/f"{stem}.pdf")
            doc=fitz.open(FIGURES/f"{stem}.pdf")
            assert len(doc)==1
            doc[0].get_pixmap(matrix=fitz.Matrix(300/72,300/72),alpha=False).save(FIGURES/f"{stem}.png")
            doc.close()
    print(f"Typeset {len(_PUB_LAYOUTS)} LaTeX panel overviews.")


def make_publication_figures():
    """Regenerate every current figure from recorded data and independent panels."""
    _PUB_LAYOUTS.clear()
    _PUB_FILES.clear()
    with plt.rc_context(_PUB_STYLE):
        _pub_composition()
        _pub_structure()
        _pub_localization()
        _pub_knockout()
        _pub_routing()
        _pub_relation_tokens()
        _pub_interaction()
        _pub_closure_and_selection()
        _pub_appendix_bars()
        make_publication_cases()
        _pub_conceptual_panels()
    _pub_compile_overviews()
    export_csv("input_manifest_publication",[
        {"path":p,"bytes":(ROOT/p).stat().st_size,
         "sha256":hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}
        for p in sorted(INPUT_PATHS)], lineterminator="\n")
    print(f"Rendered {len(_PUB_FILES)} panels/keys and {len(_PUB_LAYOUTS)} LaTeX layouts.")


# Case panels use literal recorded evidence and answer outcomes. Background
# highlights identify evidence roles; they are never token-attribution scores.
def _pub_case_canvas(width, height):
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 72 * width), ylim=(72 * height, 0))
    ax.axis('off')
    return fig, ax


def _pub_case_frame(ax, x, y, width, height, *, fill='white', edge='#B7BABE'):
    ax.add_patch(Rectangle((x, y), width, height, facecolor=fill,
                           edgecolor=edge, linewidth=.55, zorder=0))


def _pub_case_text(ax, x, y, text, *, size=8, color='#202428', weight='normal', **kwargs):
    return ax.text(x, y, text, fontsize=size, ha='left', va='top',
                   color=color, fontweight=weight, **kwargs)


def _pub_case_rich(ax, x, y, parts, width, *, size=8, leading=9.6):
    """Wrap measured words, preserving literal text and semantic highlights.

    Coordinates are typographic points, so all case panels retain their declared
    type size at the manuscript's intended inclusion width.
    """
    import re
    from matplotlib.font_manager import FontProperties
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    prop = FontProperties(family=plt.rcParams['font.family'], size=size)
    scale = 72 / fig.dpi
    xpos, ypos = x, y
    for text, fill in parts:
        for word in re.findall(r'\n|[^\S\n]+|[^\s]+', text):
            if word == '\n':
                xpos, ypos = x, ypos + leading
                continue
            advance = renderer.get_text_width_height_descent(word, prop, False)[0] * scale
            if word.isspace():
                if xpos > x:
                    xpos += advance
                continue
            visible = renderer.get_text_width_height_descent(word.rstrip(), prop, False)[0] * scale
            if xpos > x and xpos + visible > x + width + .01:
                xpos, ypos = x, ypos + leading
            if visible > width + .01:
                raise ValueError('Case-card word exceeds panel width: ' + word)
            if fill:
                ax.add_patch(Rectangle((xpos - .6, ypos - .3), visible + 1.2, size + 1.8,
                                       facecolor=fill, edgecolor='none', zorder=1))
            _pub_case_text(ax, xpos, ypos, word, size=size, zorder=2)
            xpos += advance
    return ypos + leading


def _pub_case_highlights(text, phrases):
    """Partition existing text; phrases maps literal spans to semantic colors."""
    import re
    if not phrases:
        return [(text, None)]
    pattern = re.compile('|'.join(re.escape(p) for p in sorted(phrases, key=len, reverse=True)))
    parts, offset = [], 0
    for match in pattern.finditer(text):
        if match.start() > offset:
            parts.append((text[offset:match.start()], None))
        parts.append((match.group(), phrases[match.group()]))
        offset = match.end()
    if offset < len(text):
        parts.append((text[offset:], None))
    return parts


def _pub_case_excerpt(source, fragments):
    """Ellipsize only at explicitly checked boundaries in recorded evidence."""
    cursor = 0
    for fragment in fragments:
        found = source.find(fragment, cursor)
        if found < 0:
            raise ValueError('Case excerpt is absent or out of order: ' + fragment)
        cursor = found + len(fragment)
    return '... ' + ' ... '.join(fragments) + ' ...'


def _pub_angela_card(case, *, appendix=False, width=3.25):
    height = 2.38 if appendix else 1.76
    fig, ax = _pub_case_canvas(width, height)
    w, h = width * 72, height * 72
    _pub_case_frame(ax, 1, 1, w - 2, h - 2)
    _pub_case_frame(ax, 1, 1, w - 2, 20, fill='#F2F1EF')
    _pub_case_rich(ax, 7, 5, _pub_case_highlights('Q: ' + case['question'],
        {'mother': '#F5DCCF'}), w - 14, size=8, leading=9.5)
    root = _pub_case_excerpt(case['root_evidence'], ['directed by Rebecca Miller'])
    _pub_case_text(ax, 7, 26, f"P{case['root_index']}: Angela", size=7.6, weight='bold')
    _pub_case_rich(ax, 56, 26, _pub_case_highlights(root,
        {case['bridge_title']: '#DDEAF5'}), w - 63, size=7.6, leading=9.2)
    _pub_case_text(ax, 7, 40, f"P{case['bridge_index']}: {case['bridge_title']}",
                   size=7.6, weight='bold')
    target = next(r['answer'] for r in case['arms'] if r['correct'])
    competitor = next(r['answer'] for r in case['arms'] if r['method'] == 'native')
    bridge = _pub_case_excerpt(case['bridge_evidence'],
        ['daughter of ' + competitor, 'and his third wife ' + target])
    _pub_case_rich(ax, 7, 51, _pub_case_highlights(bridge,
        {competitor: '#F4DFD9', target: '#DCECE3'}), w - 14, size=8, leading=9.6)
    arm_names = {'native': 'Native', 'mass_only': 'Mass only',
                 'conditional_only': 'Pattern only', 'both': 'Both'}
    records = {r['method']: r for r in case['arms']}
    assert set(records) == set(arm_names)
    for i, (method, label) in enumerate(arm_names.items()):
        record = records[method]
        assert record['correct'] == (method == 'both')
        y = 76 + 11.2 * i
        _pub_case_frame(ax, 6, y, w - 12, 11.2,
                        fill='#EDF5F0' if record['correct'] else '#F8F8F8', edge='#E1E3E5')
        _pub_case_text(ax, 11, y + 1.4, label, size=7.7,
                       weight='bold' if record['correct'] else 'normal')
        _pub_case_text(ax, 83, y + 1.4, record['answer'], size=8,
                       color='#286447' if record['correct'] else '#202428',
                       weight='bold' if record['correct'] else 'normal')
        if record['correct']:
            ax.text(w - 11, y + 1.6, 'correct', size=7.2, ha='right', va='top', color='#286447')
    if appendix:
        exchange = case['reciprocal_exchange']
        _pub_case_text(ax, 7, 130, 'CoReTrace: reciprocal fact exchange', size=8, weight='bold')
        _pub_case_rich(ax, 7, 143, [
            (exchange['original_answer'], '#DCECE3'), ('  →  ', None),
            (exchange['edited_answer'], '#DCECE3')], w - 14, size=8.8, leading=10.2)
        _pub_case_text(ax, 7, 158,
            f"Same address: P{case['bridge_index']} ({case['bridge_title']})", size=7.5)
    return fig


def _pub_exchange_card(case):
    exchange = case['reciprocal_exchange']
    width, height = 3.25, 1.66
    fig, ax = _pub_case_canvas(width, height)
    w, h = width * 72, height * 72
    _pub_case_frame(ax, 1, 1, w - 2, h - 2)
    _pub_case_frame(ax, 1, 1, w - 2, 20, fill='#F2F1EF')
    _pub_case_rich(ax, 7, 5, _pub_case_highlights('Q: ' + case['question'],
        {'mother': '#F5DCCF'}), w - 14, size=8, leading=9.5)
    selected = exchange['original_selected_paragraph']
    assert selected == exchange['edited_selected_paragraph'] == case['bridge_index']
    _pub_case_text(ax, 7, 26, f"Same selected address: P{selected} · {case['bridge_title']}",
                   size=7.8, weight='bold')
    for x, label, value, answer in [
            (7, 'Original', exchange['original_value'], exchange['original_answer']),
            (120, 'Edited', exchange['edited_value'], exchange['edited_answer'])]:
        _pub_case_frame(ax, x, 40, 107, 57)
        _pub_case_frame(ax, x, 40, 107, 12, fill='#F1F3F5')
        _pub_case_text(ax, x + 5, 41.8, label, size=8, weight='bold')
        _pub_case_text(ax, x + 5, 56, '... and his third wife', size=7.6)
        _pub_case_rich(ax, x + 5, 67, [(value, '#DDEAF5'), (' ...', None)], 97, size=8.4)
        ax.plot([x + 4, x + 103], [81, 81], color='#D6DADD', lw=.45)
        _pub_case_text(ax, x + 5, 85, 'Answer: ' + answer, size=8.0, color='#286447', weight='bold')
    _pub_case_text(ax, 7, 104,
        f"Reciprocal exchange with P{exchange['partner_index']}: {exchange['partner_bridge']}", size=7.2)
    return fig


def _pub_corvinus_card(case, record, *, width=3.31):
    fig, ax = _pub_case_canvas(width, 2.38)
    w, h = width * 72, 2.38 * 72
    _pub_case_frame(ax, 1, 1, w - 2, h - 2)
    _pub_case_frame(ax, 1, 1, w - 2, 20, fill='#F2F1EF')
    _pub_case_rich(ax, 7, 5, [('Q: ' + case['question'], None)], w - 14, size=8, leading=9.5)
    root, bridge, target = case['chain']
    evidence = {e['role']: e for e in record['evidence']}
    _pub_case_text(ax, 7, 26, f"P{case['root_index']}: {root}", size=7.8, weight='bold')
    first = _pub_case_excerpt(evidence['first_target']['text'], ['was the illegitimate son of ' + bridge])
    _pub_case_rich(ax, 7, 38, _pub_case_highlights(first, {bridge: '#DDEAF5'}),
                   w - 14, size=8, leading=9.6)
    _pub_case_text(ax, 7, 64, f"P{case['bridge_index']}: {bridge}", size=7.8, weight='bold')
    second = _pub_case_excerpt(evidence['second_target']['text'], ['He was the son of ' + target])
    _pub_case_rich(ax, 7, 76, _pub_case_highlights(second, {target: '#DCECE3'}),
                   w - 14, size=8, leading=9.6)
    records = [('Native · first hop', case['direct_first'], True),
               ('Native · second hop', case['direct_target'], True),
               ('Native · composed', case['native_composed'], False),
               ('CoReTrace · composed', case['final_composed'], True)]
    for i, (label, answer, correct) in enumerate(records):
        y = 102 + i * 12.5
        _pub_case_frame(ax, 6, y, w - 12, 12.5,
                        fill='#EDF5F0' if correct else '#F8EAE7', edge='#E1E3E5')
        _pub_case_text(ax, 11, y + 2, label, size=7.6)
        _pub_case_text(ax, 107, y + 2, answer, size=8, weight='bold',
                       color='#286447' if correct else '#965142')
    _pub_case_text(ax, 7, 158, 'All three models · recorded test source · run 42', size=7.2)
    return fig


def make_publication_cases():
    """Publish standalone case panels without changing records or aggregation."""
    cases = _story_cases()
    case = cases['angela']
    complete = read_json('analysis/internal/mechanism_case_records_20261125_v2.json')['cases']
    diagnostic = complete['angela']['diagnostic']
    exchange = complete['angela']['fact_exchange']
    assert all(diagnostic['checks'].values()) and all(exchange['checks'].values())
    assert case['source_id'] == complete['angela']['source_id']
    original_arms = {r['method']: r for r in diagnostic['arms']}
    for row in case['arms']:
        assert row['answer'] == original_arms[row['method']]['answer']
        assert row['correct'] == original_arms[row['method']]['correct']
    r = case['reciprocal_exchange']
    for view in ('original', 'edited'):
        assert r[view + '_answer'] == exchange[view]['answer']
        assert exchange[view]['correct']
        assert r[view + '_selected_paragraph'] == exchange[view]['selected_paragraph']
    assert r['word_bag_identical'] and r['character_bag_identical']

    # Figure 11: the exact four recorded predictions and their aggregate partition.
    _pub_save(_pub_angela_card(case), 'data_main_joint_case_revision_a')
    rows = _revision_read_rows('data_revision_joint_counts.csv')
    values = {row['model']: row for row in rows}
    assert set(values) == set(MODELS)
    joint = np.array([int(values[m]['joint_only']) for m in MODELS])
    total = np.array([int(values[m]['both_repairs']) for m in MODELS])
    errors = np.array([int(values[m]['native_errors']) for m in MODELS])
    assert np.all(0 <= joint) and np.all(joint <= total) and np.all(total <= errors)
    fig, ax = plt.subplots(figsize=(3.25, 1.08))
    fig.subplots_adjust(left=.285, right=.975, bottom=.28, top=.77)
    y = np.arange(3)[::-1]
    ax.barh(y, joint, height=.58, color='#C7865F', label='Joint only', zorder=3)
    ax.barh(y, total - joint, left=joint, height=.58, color='#CCD1D6',
            label='Single arm also correct', zorder=3)
    for yi, count, overall in zip(y, joint, total):
        ax.text(count / 2, yi, str(count), ha='center', va='center', size=8, weight='bold')
        ax.text(overall + .65, yi, str(overall), ha='left', va='center', size=7.6)
    ax.set(yticks=y, yticklabels=[MODEL_NAMES[m] for m in MODELS], xlim=(0, 33),
           xticks=[0, 10, 20, 30], ylim=(-.45, 2.45), xlabel='Native errors corrected by Both (count)')
    ax.tick_params(axis='y', length=0, pad=3, labelsize=7.5)
    ax.tick_params(axis='x', length=2, pad=2, labelsize=7.2)
    ax.xaxis.label.set_size(7.5)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.grid(axis='x', color='#E0E3E6', lw=.45, linestyle='--', zorder=0)
    ax.set_axisbelow(True)
    fig.legend(*ax.get_legend_handles_labels(), loc='upper center', bbox_to_anchor=(.51, 1.015),
               ncol=2, frameon=False, fontsize=7.2, handlelength=1, columnspacing=.7,
               handletextpad=.35, borderpad=.2)
    _pub_save(fig, 'data_main_joint_case_revision_b')
    _pub_layout('data_main_joint_case_revision', [
        [('data_main_joint_case_revision_a', 'A joint-only repair in Llama-3.1-8B', 1.0)],
        [('data_main_joint_case_revision_b', 'Joint-only corrections across models', 1.0)]])

    # Figure 12: both fact versions retain the same selected paragraph address.
    _pub_save(_pub_exchange_card(case), 'data_main_content_case_revision_a')
    rows = _revision_read_rows('data_revision_content.csv')
    values = {row['model']: row for row in rows}
    assert set(values) == set(MODELS)
    assert all(int(values[m]['stable_addresses']) == int(values[m]['pairs']) == 100 for m in MODELS)
    native = [float(values[m]['native_joint_accuracy']) for m in MODELS]
    final = [float(values[m]['final_joint_accuracy']) for m in MODELS]
    assert all(0 <= value <= 100 for value in native + final)
    fig, ax = plt.subplots(figsize=(3.25, 1.08))
    fig.subplots_adjust(left=.285, right=.975, bottom=.28, top=.77)
    for i, (yi, a, b) in enumerate(zip(y, native, final)):
        ax.plot([a, b], [yi, yi], color='#B6C3CC', lw=1.5, zorder=2)
        ax.scatter(a, yi, s=20, color='#8A929B', label='Native' if i == 0 else None, zorder=3)
        ax.scatter(b, yi, s=23, color='#4F8C73', label='CoReTrace' if i == 0 else None, zorder=3)
        ax.text(a - 3, yi, f'{a:g}', ha='right', va='center', size=7.5)
        ax.text(b + 3, yi, f'{b:g}', ha='left', va='center', size=7.5, weight='bold')
    ax.set(yticks=y, yticklabels=[MODEL_NAMES[m] for m in MODELS], xlim=(0, 100),
           xticks=[0, 50, 100], ylim=(-.45, 2.45), xlabel='Joint original / edited accuracy (%)')
    ax.tick_params(axis='y', length=0, pad=3, labelsize=7.5)
    ax.tick_params(axis='x', length=2, pad=2, labelsize=7.2)
    ax.xaxis.label.set_size(7.5)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.grid(axis='x', color='#E0E3E6', lw=.45, linestyle='--', zorder=0)
    ax.set_axisbelow(True)
    fig.legend(*ax.get_legend_handles_labels(), loc='upper center', bbox_to_anchor=(.56, 1.015),
               ncol=2, frameon=False, fontsize=7.5, handletextpad=.35, columnspacing=1,
               borderpad=.2)
    _pub_save(fig, 'data_main_content_case_revision_b')
    _pub_layout('data_main_content_case_revision', [
        [('data_main_content_case_revision_a', 'Same question, same selected address', 1.0)],
        [('data_main_content_case_revision_b', 'Joint original / edited correctness', 1.0)]])

    # A5: both policies use the same checkpoint, question and candidate graph.
    worked = read_json('outputs/figures/worked_examples.json')
    record = next(row for row in worked if row['model'] == MODELS[0])
    source = record['source']
    predictions = {(row['method'], row['query']): row for row in record['predictions']}
    order = predictions[('graphfirst', 'composed')]
    reader = predictions[('final', 'composed')]
    native_answer = predictions[('native', 'composed')]
    assert order['selection']['graph'] == reader['selection']['graph']
    assert len(order['selection']['graph']['neighbors']) == 2
    assert not order['correct'] and reader['correct'] and not native_answer['correct']
    assert predictions[('native', 'direct_first')]['correct']
    assert predictions[('native', 'direct_target')]['correct']
    assert source['original_context'][reader['selection']['chosen']][0] == source['bridge']
    width, height = 4.59, 1.83
    fig, ax = _pub_case_canvas(width, height)
    w, h = width * 72, height * 72
    _pub_case_frame(ax, 1, 1, w - 2, h - 2)
    _pub_case_frame(ax, 1, 1, w - 2, 26, fill='#F2F1EF')
    _pub_case_rich(ax, 7, 5, [('Q: ' + source['original_question'], None)], w - 14,
                   size=8.5, leading=10)
    _pub_case_text(ax, 7, 32, 'Native answer: ' + native_answer['answer'], size=7.8)
    card_width = (w - 21) / 2
    for x, label, prediction in [(7, 'Input order', order), (14 + card_width, 'Full reader', reader)]:
        index = prediction['selection']['chosen']
        title, sentences = source['original_context'][index]
        _pub_case_frame(ax, x, 46, card_width, 79)
        _pub_case_frame(ax, x, 46, card_width, 28, fill='#F1F3F5')
        _pub_case_rich(ax, x + 5, 49, [(f'P{index}: ' + title, None)], card_width - 10,
                       size=8, leading=9.4)
        if prediction['correct']:
            excerpt = next(s for s in sentences if 'He died in 1751' in s)
            parts = _pub_case_highlights(excerpt, {prediction['answer']: '#DCECE3'})
        else:
            sentence = next(s for s in sentences if 'Melusina may have been the mother' in s)
            excerpt = _pub_case_excerpt(sentence,
                ['Melusina may have been the mother', 'of Benedict Swingate Calvert'])
            parts = _pub_case_highlights(excerpt, {'mother': '#F5DCCF'})
        _pub_case_rich(ax, x + 5, 78, parts, card_width - 10, size=7.8, leading=9.2)
        _pub_case_frame(ax, x, 110, card_width, 15,
                        fill='#EDF5F0' if prediction['correct'] else '#F8EAE7', edge='#E1E3E5')
        _pub_case_text(ax, x + 5, 112.5, label + ' → ' + prediction['answer'], size=8.1,
                       weight='bold', color='#286447' if prediction['correct'] else '#965142')
    _pub_save(fig, 'data_main_case')

    # A8: shared outcome columns are used only after checking all three models.
    corvinus = cases['corvinus']
    assert set(corvinus['models']) == set(MODELS)
    for result in complete['corvinus']['model_results']:
        native = result['native_answers']
        assert native['direct_first']['correct'] and native['direct_target']['correct']
        assert not native['composed']['correct'] and result['coretrace_composed']['correct']
        for key in ('direct_first', 'direct_target'):
            assert corvinus[key] == native[key]['answer']
        assert corvinus['native_composed'] == native['composed']['answer']
        assert corvinus['final_composed'] == result['coretrace_composed']['answer']
    _pub_save(_pub_corvinus_card(corvinus, complete['corvinus']), 'data_main_mechanism_cases_a')
    _pub_save(_pub_angela_card(case, appendix=True, width=3.31), 'data_main_mechanism_cases_b')
    _pub_layout('data_main_mechanism_cases', [[
        ('data_main_mechanism_cases_a', 'Correct hops, failed composition', .49),
        ('data_main_mechanism_cases_b', 'Access-dependent local reading', .49)]])



def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    tasks = {
        "composition": lambda: make_composition(seeds),
        "diagnosis": lambda: make_diagnosis(seeds),
        "causal": make_causal, "content": lambda: make_content(seeds),
        "localization": make_localization, "necessity": make_necessity,
        "ablation": lambda: make_ablation(seeds),
        "capabilities": lambda: make_capabilities(seeds),
        "ambiguity": make_ambiguity, "case": make_case,
        "mechanism_cases": make_mechanism_cases,
        "mechanism_causality": make_mechanism_causality,
        "joint_rescue": make_joint_rescue, "address_routing": make_address_routing,
        "mechanism_structure": make_mechanism_structure,
        "composition_address": make_composition_address,
        "story_revision": make_story_revision, "story_polish": make_story_polish,
        "publication": make_publication_figures,
    }
    parser.add_argument("--only", nargs="*", choices=list(tasks))
    args = parser.parse_args()
    seeds = read_json("configs/experiments.json")["seeds"]
    legacy_tasks = list(dict.fromkeys(name for name in (args.only or []) if name != "publication"))
    if any(name in legacy_tasks for name in ("localization", "necessity")):
        legacy_tasks = list(dict.fromkeys(legacy_tasks + ["localization", "necessity"]))
    collected = {name: tasks[name]() for name in legacy_tasks}
    if "localization" in collected and "necessity" in collected:
        render_head_pair(collected["localization"], *collected["necessity"])
    # Always render the current publication assets last, even when a legacy
    # data-reconstruction task was explicitly requested alongside publication.
    make_publication_figures()
    requested = legacy_tasks + ["publication"]
    manifest_name = "input_manifest_publication" if requested == ["publication"] else "input_manifest_" + "_".join(requested)
    export_csv(manifest_name, [
        {"path": p, "bytes": (ROOT / p).stat().st_size,
         "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
        for p in sorted(INPUT_PATHS)
    ], lineterminator="\n")
    print(f"Read {len(INPUT_PATHS)} input files; see analysis/figure_data/{manifest_name}.csv")


if __name__ == "__main__":
    main()
