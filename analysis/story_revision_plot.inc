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
