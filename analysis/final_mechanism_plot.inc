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
