#!/usr/bin/env python3
"""Render the final CoReTrace manuscript figures in the original Git checkout.

The existing numerical pipeline is loaded from its immutable, verified Git blob;
the final manuscript renderers below are the only overrides. This preserves the
original analysis functions and requires the repository's baseline commit to be
present locally. No network access or additional scripts are required.
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
    }
    parser.add_argument("--only", nargs="*", choices=list(tasks))
    args = parser.parse_args()
    seeds = read_json("configs/experiments.json")["seeds"]
    requested = list(args.only or [name for name in tasks if name != "story_polish"])
    if any(name in requested for name in ("localization", "necessity")):
        requested = list(dict.fromkeys(requested + ["localization", "necessity"]))
    collected = {name: tasks[name]() for name in requested}
    if "localization" in collected and "necessity" in collected:
        render_head_pair(collected["localization"], *collected["necessity"])
    manifest_name = "input_manifest" if not args.only else "input_manifest_" + "_".join(args.only)
    export_csv(manifest_name, [
        {"path": p, "bytes": (ROOT / p).stat().st_size,
         "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
        for p in sorted(INPUT_PATHS)
    ], lineterminator="\n" if requested == ["story_revision"] else "\r\n")
    print(f"Read {len(INPUT_PATHS)} input files; see analysis/figure_data/{manifest_name}.csv")


if __name__ == "__main__":
    main()
