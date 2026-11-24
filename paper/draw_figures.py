"""Editable manuscript-only Figures 1--3 (native PowerPoint vectors).

These are explanatory diagrams, separate from scripts/figures.py's measured
result plots. All examples and response strings are read from formal artifacts.
No synthetic heatmap is presented as a measured localization result.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE, MSO_PATTERN
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
WHITE='FFFFFF'; INK='171717'; GRAY='737373'; LIGHT='D8D8D8'
BLUE='BBCBE9'; PALEBLUE='EEF2FA'; NAVY='345A8D'
TEAL='79BDB7'; PALETEAL='EDF7F4'; DARKTEAL='277B71'
ORANGE='D49458'; PALEORANGE='FCF1E7'; BROWN='985322'
RED='BE3030'; PALERED='FBECEC'; PURPLE='7561AE'; PALEPURPLE='F7F4FD'
SERIF='Liberation Serif'; MONO='Liberation Mono'
W,H=16,8.5


def example():
    sid='df212d0e0bda11eba7f7acde48001122'
    folder=ROOT/'data/CoRe-2Wiki-v1.0'
    source=next(r for r in map(json.loads,(folder/'corpus.jsonl').open()) if r['source_id']==sid)
    queries={r['query']:r for r in map(json.loads,(folder/'queries.jsonl').open()) if r['source_id']==sid}
    predpath=ROOT/'outputs/llama3_8b/seed42/evaluation/core/predictions.jsonl'
    status=json.loads(predpath.with_name('manifest.json').read_text())
    assert status['status']=='COMPLETE'
    pred={(r['method'],r['query']):r for r in map(json.loads,predpath.open()) if r['source_id']==sid}
    assert pred['native','direct_first']['correct'] and pred['native','direct_target']['correct']
    assert not pred['native','composed']['correct'] and pred['final','composed']['correct']
    quads=list(map(json.loads,(folder/'mechanism_views/discovery25_quadruplets.jsonl').open()))
    quad=next(q for q in quads if q['bridges']==['Jürgen Knieper','Duke Ellington'])
    return dict(source=source,queries=queries,pred=pred,quad=quad,files=[str(folder/'corpus.jsonl'),str(folder/'queries.jsonl'),str(predpath),str(folder/'mechanism_views/discovery25_quadruplets.jsonl')])


class Art:
    def __init__(self):
        self.prs=Presentation(); self.prs.slide_width=Inches(W); self.prs.slide_height=Inches(H)
        self.slide=self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self.slide.background.fill.solid(); self.slide.background.fill.fore_color.rgb=RGBColor.from_string(WHITE)

    def text(self,x,y,w,h,s,size=20,color=INK,bold=False,italic=False,align='left',font=SERIF,margin=.01):
        sh=self.slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
        tf=sh.text_frame; tf.word_wrap=True
        tf.margin_left=tf.margin_right=Inches(margin); tf.margin_top=tf.margin_bottom=0
        tf.vertical_anchor=MSO_ANCHOR.MIDDLE
        for i,line in enumerate(s.split('\n')):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text=line
            p.alignment={'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}[align]
            p.font.name=font; p.font.size=Pt(size); p.font.bold=bold; p.font.italic=italic
            p.font.color.rgb=RGBColor.from_string(color); p.space_before=p.space_after=Pt(0)
            p.line_spacing=1.0
        return sh

    def shape(self,x,y,w,h,fill=WHITE,line=INK,width=1.3,round=False,dash=False,shadow=False,pattern=False,kind=None):
        if shadow:
            self.shape(x+.037,y+.041,w,h,'E6E6E6',None,width,round,False,False,False,kind)
        sh=self.slide.shapes.add_shape(kind or (MSO_SHAPE.ROUNDED_RECTANGLE if round else MSO_SHAPE.RECTANGLE),Inches(x),Inches(y),Inches(w),Inches(h))
        if round: sh.adjustments[0]=.07
        if fill is None: sh.fill.background()
        elif pattern:
            sh.fill.patterned(); sh.fill.pattern=MSO_PATTERN.LIGHT_DOWNWARD_DIAGONAL
            sh.fill.fore_color.rgb=RGBColor.from_string(fill); sh.fill.back_color.rgb=RGBColor.from_string(WHITE)
        else: sh.fill.solid(); sh.fill.fore_color.rgb=RGBColor.from_string(fill)
        if line is None: sh.line.fill.background()
        else: sh.line.color.rgb=RGBColor.from_string(line); sh.line.width=Pt(width)
        if dash: sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH
        sh._element.spPr.append(OxmlElement('a:effectLst'))
        for ref in sh._element.xpath('./p:style/a:effectRef'):
            ref.set('idx','0')
        return sh

    def line(self,x1,y1,x2,y2,color=INK,width=1.4,arrow=False,dash=False):
        sh=self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2))
        sh.line.color.rgb=RGBColor.from_string(color);sh.line.width=Pt(width)
        sh._element.spPr.append(OxmlElement('a:effectLst'))
        for ref in sh._element.xpath('./p:style/a:effectRef'): ref.set('idx','0')
        if dash: sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH
        if arrow:
            en=OxmlElement('a:tailEnd');en.set('type','triangle');en.set('w','sm');en.set('len','sm');sh.line._get_or_add_ln().append(en)
        return sh

    def path(self,pts,color=INK,width=1.5,arrow=True,dash=False):
        for i,((x,y),(xx,yy)) in enumerate(zip(pts,pts[1:])): self.line(x,y,xx,yy,color,width,arrow and i==len(pts)-2,dash)

    def label(self,x,y,w,h,s,fill=PALEBLUE,color=INK,size=19,line=None,bold=False,italic=False):
        self.shape(x,y,w,h,fill,line or color,.9,round=False)
        self.text(x+.025,y,w-.05,h,s,size,color,bold,italic,'center')

    def group(self,x,y,w,h,title,color=INK,fill=PALEPURPLE,size=24):
        self.shape(x,y,w,h,fill,color,1.5,round=True,dash=True,shadow=True,pattern=True)
        self.text(x+.15,y+.06,w-.3,.42,title,size,bold=True)

    def circle(self,x,y,d,s,fill=WHITE,color=INK,size=18):
        self.shape(x,y,d,d,fill,color,1.3,kind=MSO_SHAPE.OVAL)
        self.text(x,y,d,d,s,size,color,italic=True,align='center')

    def doc(self,x,y,w,h,title,body=None,color=NAVY,fill=WHITE,size=17):
        self.shape(x+.06,y+.06,w,h,WHITE,LIGHT,.65)
        self.shape(x,y,w,h,fill,LIGHT,1,shadow=True)
        self.text(x+.10,y+.05,w-.20,.36,title,20,color,bold=True,italic=True)
        self.line(x+.1,y+.46,x+w-.1,y+.46,color,.8)
        if body: self.text(x+.12,y+.53,w-.24,h-.59,body,size)
        else:
            for j in range(3): self.line(x+.12,y+.63+j*.16,x+w-.18-(j%2)*.15,y+.63+j*.16,LIGHT,1.2)

    def tokenseq(self,x,y,labels,colors=None,widths=None,h=.43,size=17,gap=.045):
        widths=widths or [.65]*len(labels);colors=colors or [LIGHT]*len(labels)
        centers=[]
        for t,co,w in zip(labels,colors,widths):
            self.label(x,y,w,h,t,fill=co,color=INK,size=size,line=co)
            centers.append((x+w/2,y+h/2));x+=w+gap
        return centers

    def transformer(self,x,y,w,h,heads=True):
        self.shape(x,y,w,h,WHITE,INK,1.8,round=True,shadow=True,pattern=True)
        self.text(x,y+.06,w,.36,'Shared LLM',16.5,bold=True,italic=True,align='center')
        for j,t in enumerate(['Layer 1','Layer ℓ','Layer L']):
            yy=y+.57+j*(h-.95)/3
            self.label(x+.13,yy,w-.26,.35,t,PALEBLUE,size=16,line=INK)
            if heads and j==1:
                for k in range(3): self.shape(x+.18+k*(w-.34)/3,yy+.40,(w-.46)/3,.20,TEAL if k==1 else LIGHT,None)
            if j<2: self.line(x+w/2,yy+.65,x+w/2,yy+(h-.95)/3-.03,INK,1.2,True)
        self.text(x,y+h-.38,w,.28,'⋯',25,align='center')

    def heading(self,x,y,w,s,size=25): self.text(x,y,w,.45,s,size,bold=True)
    def save(self,path): self.prs.save(path)


def fig1(e):
    a=Art()
    a.heading(.23,.09,8.7,'(a) Correct in isolation, wrong in composition')
    # Actual evidence: content is an excerpt of original supporting sentences.
    a.doc(.35,.72,4.12,1.92,'Walter II of Avesnes',e['source']['edges']['first_target']['text'],color=NAVY,size=20)
    a.doc(4.79,.72,4.12,1.92,'James of Avesnes',e['source']['edges']['second_target']['text'],color=DARKTEAL,size=18)
    a.text(.4,2.73,8.5,.28,'Same 10 original Wikipedia paragraphs for every query',17,GRAY,italic=True,align='center')
    a.label(.56,3.13,2.6,.46,'Walter II of Avesnes',PALEBLUE,size=19,line=NAVY)
    a.label(3.78,3.13,2.55,.46,'James of Avesnes',PALETEAL,size=19,line=DARKTEAL)
    a.label(7.15,3.13,1.55,.46,'Arsuf',PALEORANGE,size=20,line=BROWN)
    a.line(3.18,3.36,3.75,3.36,NAVY,1.7,True);a.text(3.19,3.68,.55,.23,'father',15,NAVY,italic=True,align='center')
    a.line(6.35,3.36,7.12,3.36,DARKTEAL,1.7,True);a.text(6.35,3.68,.78,.25,'died in',15,DARKTEAL,italic=True,align='center')
    a.transformer(5.38,4.05,1.40,3.50)
    ys=[4.18,5.36,6.54]
    specs=[('direct_first','Hop 1',DARKTEAL),('direct_target','Hop 2',DARKTEAL),('composed','Multi-hop',RED)]
    for y,(q,name,co) in zip(ys,specs):
        a.text(.42,y-.25,4.55,.25,name,17,co,bold=True,italic=True)
        a.shape(.4,y+.07,4.53,.78,WHITE,LIGHT,1,shadow=True)
        a.text(.51,y+.12,4.30,.68,e['queries'][q]['question'],19)
        a.line(4.96,y+.45,5.33,y+.45,co,1.6,True)
        a.line(6.83,y+.45,7.14,y+.45,co,1.6,True)
        a.text(7.2,y+.12,1.58,.64,e['pred']['native',q]['answer'],20,co,bold=True,align='center')
        # vector verdict marks avoid emoji/font substitution
        if q!='composed': a.path([(8.55,y+.8),(8.64,y+.91),(8.84,y+.66)],DARKTEAL,2.4,False)
        else:
            a.line(8.61,y+.68,8.84,y+.91,RED,2.2);a.line(8.61,y+.91,8.84,y+.68,RED,2.2)
    a.text(.43,7.80,8.4,.27,'Llama-3.1-8B-Instruct · frozen test example · greedy native responses',16,GRAY,italic=True)
    a.line(9.10,.1,9.10,8.09,LIGHT,1)
    a.heading(9.35,.09,6.3,'(b) Three separable functional operations')
    # Recoverable information: heads to paragraph features to a readout.
    a.group(9.39,.72,6.25,2.12,'1. Recover the bridge address')
    a.label(9.60,1.40,1.72,.44,'Composed q',PALEBLUE,size=18,line=NAVY)
    for k in range(3): a.circle(11.65+k*.43,1.43,.30,'h',TEAL if k==1 else WHITE,size=15)
    a.line(11.34,1.63,11.61,1.63,NAVY,1.5,True)
    for j,t in enumerate(['p₁','p₂','p₃']):
        a.label(13.30+j*.60,1.38,.48,.44,t,PALETEAL if j==1 else 'F0F0F0',size=17,line=DARKTEAL if j==1 else GRAY)
        a.path([(12.98,1.58),(13.14,1.18),(13.54+j*.60,1.18),(13.54+j*.60,1.34)],DARKTEAL,1.0,True)
    a.text(9.61,2.02,1.86,.55,'Paragraph\nattention features',16,italic=True)
    a.line(11.50,2.25,12.02,2.25,PURPLE,1.6,True)
    a.label(12.09,2.00,1.30,.49,'Linear reader',PALEPURPLE,size=15,line=PURPLE)
    a.line(13.43,2.25,13.85,2.25,PURPLE,1.6,True)
    a.text(13.91,1.97,1.52,.56,'James of\nAvesnes',19,DARKTEAL,bold=True,align='center')
    # Access mass is not a literal full simulated attention heatmap.
    a.group(9.39,3.04,6.25,2.12,'2. Allocate evidence access')
    a.label(9.64,3.84,1.12,.48,'Query q',PALEBLUE,size=18,line=NAVY)
    a.circle(11.13,3.80,.55,'Hℓ,ₕ',TEAL,size=18)
    a.line(10.80,4.07,11.09,4.07,NAVY,1.6,True)
    for j,(xx,co) in enumerate([(12.26,LIGHT),(13.36,TEAL),(14.46,LIGHT)]):
        a.doc(xx,3.72,.84,.73,'p₂' if j==1 else ('p₁' if j==0 else 'p₃'),color=DARKTEAL if j==1 else GRAY)
        a.path([(11.72,4.08),(11.94,3.60),(xx+.42,3.60),(xx+.42,3.69)],DARKTEAL if j==1 else GRAY,2.5 if j==1 else .7,True)
    a.text(9.64,4.56,2.04,.50,'Paragraph mass mₚ',17,italic=True)
    # Disjoint paragraph groups in a single attention distribution.
    a.tokenseq(12.20,4.57,['·','·','·','·','·','·','·','·'],[LIGHT,LIGHT,TEAL,TEAL,TEAL,LIGHT,LIGHT,LIGHT],widths=[.31]*8,h=.30,size=13,gap=.04)
    a.text(12.12,4.94,3.06,.20,'Root  ·  bridge  ·  distractors',14,GRAY,align='center')
    a.group(9.39,5.36,6.25,2.36,'3. Read relation-conditioned content')
    a.text(9.64,6.04,5.56,.36,'James of Avesnes · original paragraph',19,DARKTEAL,bold=True,italic=True)
    a.tokenseq(9.65,6.56,['At the','Battle of','Arsuf,','James','…'],[WHITE,WHITE,PALEORANGE,WHITE,WHITE],widths=[.9,1.14,.83,.78,.28],h=.38,size=17)
    a.label(9.65,7.12,1.10,.36,'die where?',PALEBLUE,size=14,line=NAVY)
    a.line(10.81,7.30,11.54,7.30,NAVY,1.6,True)
    a.circle(11.60,7.05,.44,'H',TEAL,size=18)
    a.path([(12.05,7.28),(12.56,7.28),(12.56,6.98)],BROWN,1.6,True)
    a.line(12.98,7.28,13.54,7.28,BROWN,1.6,True)
    a.text(13.59,7.02,1.64,.44,'Arsuf',23,BROWN,bold=True,align='center')
    a.text(9.45,7.98,6.14,.24,'Address information → evidence access → local content use',15,GRAY,italic=True)
    return a


def fig2(e):
    a=Art()
    a.heading(.25,.08,15.4,'(a) Discover the heads whose evidence access changes with the question')
    # Identical evidence, contrasting query roles.
    a.shape(.25,.68,4.57,2.84,PALEBLUE,NAVY,1.35,round=True,shadow=True)
    a.text(.43,.73,4.20,.34,'Same evidence, paired questions',21,bold=True,italic=True,align='center')
    for j in range(7): a.shape(.57+j*.56,1.23,.44,.35,TEAL if j==3 else LIGHT,None)
    a.text(.48,1.68,4.08,.24,'Composed query',17,NAVY,bold=True,italic=True)
    a.shape(.46,1.98,4.12,.51,WHITE,LIGHT,.8)
    a.text(.56,2.00,3.94,.47,"Where did Walter’s father die?",19)
    a.text(.48,2.62,4.08,.24,'Direct-target donor',17,DARKTEAL,bold=True,italic=True)
    a.shape(.46,2.91,4.12,.43,WHITE,LIGHT,.8)
    a.text(.56,2.93,3.94,.39,'Where did James of Avesnes die?',19)
    a.transformer(5.25,.70,1.58,2.80)
    a.line(4.85,2.22,5.19,2.22,NAVY,1.8,True);a.line(4.85,3.11,5.19,3.11,DARKTEAL,1.8,True)
    a.line(6.88,2.11,7.16,2.11,NAVY,1.5,True)
    a.text(7.18,.75,3.60,.32,'Paired bridge-attention gap',21,bold=True,italic=True,align='center')
    # Schematic grid labels prevent confusing illustration with measured heatmaps.
    for r in range(5):
        for k in range(9):
            selected=(r,k) in {(1,3),(2,5),(2,6),(3,2),(3,6),(4,4)}
            a.shape(7.72+k*.285,1.33+r*.29,.25,.25,ORANGE if selected else 'EAEAEA',WHITE,.4)
    a.text(7.72,2.85,2.53,.25,'Attention head h',16,italic=True,align='center')
    sh=a.text(6.98,1.90,.85,.26,'Layer ℓ',16,italic=True,align='center');sh.rotation=270
    a.text(7.42,3.18,3.1,.23,'Schematic head ranking',15,GRAY,italic=True,align='center')
    a.line(10.54,2.11,11.03,2.11,BROWN,1.8,True)
    a.text(11.15,.76,4.13,.36,'Causal selection and necessity',21,bold=True,italic=True,align='center')
    for j,n in enumerate([20,40,80]):
        a.label(11.23+j*1.37,1.43,1.13,.49,f'Top {n}',PALEORANGE,size=20,line=BROWN)
        a.line(11.79+j*1.37,1.95,11.79+j*1.37,2.24,BROWN,1.4,True)
    a.text(11.14,2.32,4.28,.52,'Discovery accuracy → fixed head set',18,align='center')
    a.line(11.13,2.97,15.50,2.97,LIGHT,.8)
    a.text(11.19,3.07,4.27,.31,'Test: selected vs. random knockout',17,align='center')
    # Two genuinely causal operations, actual 2x2 factorization.
    a.group(.25,3.85,7.62,4.16,'(b) Separate access mass from local reading',color=NAVY,fill=PALEBLUE)
    a.text(.54,4.43,3.35,.36,'Aₚ = mₚ × αₚ',25,NAVY,bold=True,italic=True,align='center')
    a.text(4.15,4.39,3.28,.45,'Donor: normalized α only',18,DARKTEAL,italic=True,align='center')
    a.text(.49,4.96,1.12,.38,'Mass mₚ',18,italic=True,align='center')
    a.text(1.81,4.96,2.37,.38,'Receiver α',19,italic=True,align='center')
    a.text(4.58,4.96,2.42,.38,'Donor α',19,DARKTEAL,italic=True,align='center')
    a.text(.42,5.59,1.17,.41,'Native',19,italic=True,align='center')
    a.text(.42,6.56,1.17,.41,'Fixed τ',19,NAVY,italic=True,align='center')
    for row in range(2):
        for col in range(2):
            xx=1.77+col*2.8;yy=5.43+row*.98
            a.shape(xx,yy,2.48,.80,WHITE,NAVY if row else LIGHT,1)
            a.text(xx+.04,yy+.02,2.40,.27,[['Native','Conditional only'],['Mass only','Both']][row][col],18,bold=True,align='center')
            # Symbolic bars show the factor being exchanged, never effect sizes.
            heights=([.09,.14,.10,.11,.08] if col==0 else [.05,.07,.29,.06,.05])
            for j,h in enumerate(heights):
                scale=1.13 if row else .72
                a.shape(xx+.35+j*.35,yy+.70-h*scale,.25,h*scale,TEAL if col else BLUE,None)
    a.text(.49,7.48,6.95,.29,'Receiver V and O unchanged · identity preserves generated tokens',17,GRAY,italic=True,align='center')
    a.group(8.10,3.85,7.65,4.16,'(c) Does the answer follow the edited local fact?',color=BROWN,fill=PALEORANGE)
    a.text(8.32,4.44,3.1,.31,'Original context',20,bold=True,italic=True,align='center')
    a.text(12.19,4.44,3.12,.31,'Reciprocal value swap',20,bold=True,italic=True,align='center')
    a.text(8.35,4.94,3.25,.33,'Jürgen Knieper',20,DARKTEAL,bold=True,italic=True)
    a.text(8.35,5.31,1.02,.39,'Born in',19)
    a.label(9.38,5.30,1.34,.41,'Karlsruhe',PALETEAL,size=19,line=DARKTEAL)
    a.text(10.78,5.31,.60,.39,', …',19)
    a.text(8.35,6.06,3.26,.33,'Duke Ellington',20,NAVY,bold=True,italic=True)
    a.text(8.35,6.43,1.02,.40,'Born in',19)
    a.label(9.38,6.43,1.57,.41,'Washington',PALEBLUE,size=18,line=NAVY)
    a.text(11.0,6.44,.72,.39,', D.C.,',17)
    a.text(12.35,4.94,3.01,.33,'Jürgen Knieper',20,DARKTEAL,bold=True,italic=True)
    a.text(12.35,5.31,1.02,.39,'Born in',19)
    a.label(13.38,5.30,1.57,.41,'Washington',PALEBLUE,size=18,line=NAVY)
    a.text(15.0,5.31,.55,.39,', …',19)
    a.text(12.35,6.06,3.01,.33,'Duke Ellington',20,NAVY,bold=True,italic=True)
    a.text(12.35,6.43,1.02,.39,'Born in',19)
    a.label(13.38,6.43,1.34,.41,'Karlsruhe',PALETEAL,size=19,line=DARKTEAL)
    a.text(14.78,6.44,.79,.39,', D.C.,',17)
    a.line(11.75,5.58,12.15,6.52,DARKTEAL,1.7,True)
    a.line(11.75,6.52,12.15,5.58,NAVY,1.7,True)
    a.text(8.39,7.13,6.98,.29,'Same question · same word and character counts',17,GRAY,italic=True,align='center')
    a.text(8.39,7.54,6.98,.25,'Measure: edited-value following and obsolete-answer persistence',17,BROWN,italic=True,align='center')
    a.text(.29,8.16,15.32,.23,'Controlled probes use the original, shared-context discovery quadruplets; all four endpoints remain in the evidence.',16,GRAY,italic=True,align='center')
    return a


def fig3(e):
    a=Art()
    a.heading(.25,.08,15.3,'(a) Tune selected heads and scope their prefill updates')
    # Training route, transparent selected components.
    a.shape(.42,.89,2.29,1.93,WHITE,LIGHT,.7)
    a.shape(.36,.83,2.29,1.93,WHITE,LIGHT,1,shadow=True)
    a.text(.49,.96,2.02,.62,'Composed\ntraining QA',20,NAVY,bold=True,italic=True,align='center')
    a.text(.50,1.64,2.02,.67,'2,000 real sources\nAnswer-only CE',19,align='center')
    a.line(2.77,1.78,3.13,1.78,INK,1.7,True)
    a.shape(3.20,.82,3.47,1.96,WHITE,INK,1.6,round=True,shadow=True)
    a.text(3.33,.92,3.20,.33,'Selected-head tuning',22,bold=True,italic=True,align='center')
    for j,s in enumerate(['Q','K','V','O']):
        a.label(3.53+j*.72,1.57,.54,.45,s,PALEORANGE,size=22,line=BROWN,bold=True)
        a.text(3.49+j*.72,2.12,.63,.32,'θ + Δ',16,BROWN,italic=True,align='center')
    a.line(6.72,1.79,7.12,1.79,BROWN,1.7,True)
    a.text(7.23,.85,3.56,.35,'Scoped native projection',22,bold=True,italic=True,align='center')
    # Actual mask concept: token columns, component rows. No unverified layers.
    a.text(7.58,1.25,1.39,.27,'Context prefix',16,italic=True,align='center')
    a.text(9.12,1.25,1.06,.27,'Question',16,italic=True,align='center')
    a.text(10.27,1.25,.87,.27,'Decode',16,italic=True,align='center')
    for r,s in enumerate(['Q / K','V / O']):
        a.text(7.08,1.68+r*.48,.54,.30,s,16,italic=True,align='center')
        for k in range(8):
            native=r==1 and k<3
            a.shape(7.68+k*.42,1.67+r*.48,.37,.34,BLUE if native else ORANGE,None)
    a.text(7.61,2.64,3.57,.23,'Illustrative prefill mask',15,GRAY,italic=True,align='center')
    a.line(11.30,.91,11.30,2.82,LIGHT,.9)
    a.text(11.52,.85,4.02,.34,'Fixed prefill scopes',22,bold=True,italic=True,align='center')
    a.text(11.53,1.44,4.04,.31,'Qwen 4B:  V/O · L16–19 · prefix',18)
    a.text(11.53,1.92,4.04,.31,'Qwen 8B:  V/O · L12–19 · question',18)
    a.text(11.53,2.40,4.04,.31,'Llama 8B: V · selected layers · prefix',18)
    a.shape(3.47,3.04,.19,.19,ORANGE,None);a.text(3.73,2.98,2.32,.31,'Trained projection',17,italic=True)
    a.shape(6.12,3.04,.19,.19,BLUE,None);a.text(6.38,2.98,4.39,.31,'Native selected slices at masked positions',17,italic=True)
    a.text(11.61,2.97,3.87,.31,'Cached decoding stays trained',18,BROWN,bold=True,italic=True)
    a.line(.27,3.50,15.69,3.50,INK,1)
    a.heading(.25,3.66,15.3,'(b) Decode the bridge address, preserve evidence text, and answer')
    # Input-derived graph, showing actual ambiguous candidates.
    a.text(.39,4.34,2.91,.31,'Input title graph',22,bold=True,italic=True,align='center')
    a.label(.49,4.98,2.66,.48,'Walter II of Avesnes',PALEBLUE,size=20,line=NAVY)
    a.path([(1.82,5.48),(1.82,5.76),(.99,5.76),(.99,6.02)],GRAY,1.3,True)
    a.path([(1.82,5.48),(1.82,5.76),(2.62,5.76),(2.62,6.02)],DARKTEAL,1.6,True)
    a.label(.35,6.06,1.33,.63,'Walter II',WHITE,size=18,line=GRAY)
    a.label(1.87,6.06,1.62,.63,'James of\nAvesnes',PALETEAL,size=18,line=DARKTEAL)
    a.text(.43,7.00,2.85,.56,'Candidate paragraphs from\nexplicit title mentions',17,GRAY,italic=True,align='center')
    a.line(3.56,5.92,3.93,5.92,INK,1.6,True)
    # Attention head by candidate matrix, linear scores, chosen bridge.
    a.text(4.01,4.27,3.17,.57,'State-aligned\naddress reader',20,bold=True,italic=True,align='center')
    a.text(4.53,4.79,1.15,.24,'p₁     p₂',15,italic=True,align='center')
    for row in range(4):
        a.text(3.99,5.02+row*.31,.49,.26,['h₁','h₂','⋮','h'][row],16,italic=True,align='center')
        if row==3: a.text(4.28,6.07,.13,.16,'H',11,italic=True,align='center')
        for col in range(2): a.shape(4.62+col*.55,5.03+row*.31,.43,.25,TEAL if col else BLUE,WHITE,.4)
    a.text(4.08,6.27,2.03,.43,'fₚ: mean / last\n+ metadata',13.5,GRAY,italic=True,align='center')
    a.line(5.80,5.64,6.08,5.64,PURPLE,1.4,True)
    a.circle(6.15,5.34,.62,'wᵀf',PALEPURPLE,PURPLE,size=19)
    a.line(6.48,6.02,6.48,6.62,PURPLE,1.5,True)
    a.label(4.25,6.73,2.88,.48,'James of Avesnes',PALETEAL,size=21,line=DARKTEAL,bold=True)
    a.text(4.10,7.39,3.16,.45,'One extra prefill only\nfor ambiguous candidates',16,GRAY,italic=True,align='center')
    a.line(7.21,6.96,7.63,6.96,DARKTEAL,1.7,True)
    # Input filtering is literal original paragraphs, no summaries.
    a.text(7.68,4.34,3.25,.31,'Original evidence text',22,bold=True,italic=True,align='center')
    a.doc(7.82,4.93,2.86,.86,'Walter II of Avesnes',color=NAVY)
    a.doc(7.82,5.95,2.86,.86,'James of Avesnes',color=DARKTEAL,fill=PALETEAL)
    a.label(7.82,7.06,2.86,.42,'Original question',WHITE,size=19,line=GRAY)
    a.text(7.80,7.63,2.90,.27,'Root + decoded bridge',17,GRAY,italic=True,align='center')
    a.line(10.83,6.07,11.24,6.07,INK,1.7,True)
    # Concrete token-time scope: reader and generation share same body.
    a.shape(11.34,4.83,4.20,2.88,WHITE,INK,1.7,round=True,shadow=True)
    a.text(11.50,4.98,3.90,.33,'Same scoped LLM',23,bold=True,italic=True,align='center')
    a.label(11.64,5.64,1.45,.49,'Prefill',PALEBLUE,size=20,line=NAVY)
    a.line(13.15,5.89,13.52,5.89,INK,1.4,True)
    a.label(13.57,5.64,1.62,.49,'Decode',PALEORANGE,size=20,line=BROWN)
    a.tokenseq(11.69,6.36,['·','·','·','q'],[BLUE,BLUE,BLUE,ORANGE],widths=[.27]*4,h=.30,size=15,gap=.05)
    a.tokenseq(13.68,6.36,['y₁','y₂','…'],[ORANGE]*3,widths=[.35]*3,h=.30,size=14)
    a.line(13.41,6.85,13.41,7.03,DARKTEAL,1.5,True)
    a.text(12.18,7.05,2.50,.47,e['pred']['final','composed']['answer'],26,DARKTEAL,bold=True,align='center')
    a.path([(14.51,7.26),(14.64,7.40),(14.89,7.08)],DARKTEAL,2.4,False)
    a.text(.28,8.14,15.38,.25,'Deployment uses input title links and a frozen train-only reader; support annotations and answer labels are absent at inference.',16,GRAY,italic=True,align='center')
    return a


CAPTIONS={
'figure1':'A contextual composition failure and the functional operations studied. Left: exact supporting sentences and native responses from one frozen CoRe-2Wiki test source. Each constituent question is answered correctly under the same ten-paragraph evidence, while the composed question fails. Right: bridge-address recovery, paragraph-access allocation, and relation-conditioned content reading are distinct operations tested by the study. Their arrangement does not assert three exclusive consecutive layer ranges.',
'figure2':'Causal diagnosis of contextual composition. (a) Shared-context direct-target/composed queries reveal question-sensitive paragraph access; head counts are selected on discovery data, with selected versus layer-matched random knockout on test sources. (b) A factorial intervention independently changes paragraph mass and the within-paragraph conditional attention donated by a direct-target query, leaving receiver values and output projections unchanged. (c) Reciprocal object-surface exchange tests whether answers follow local evidence while preserving global word and character counts. The shared-context factorization and content interventions use the frozen discovery quadruplets. All colored head grids and bars are schematics, not measured effect sizes.',
'figure3':'Mechanism-derived repair. (a) Answer-only tuning updates selected heads; native projection slices are restored only at fixed model-specific prefill positions, while cached decoding retains trained weights. The token mask is illustrative; exact per-model scopes are listed. (b) An input title graph supplies candidate paragraphs, a reader fitted on training-only paragraph features selects the bridge when candidates are ambiguous, and the original root and chosen bridge text are passed to the same scoped model. The feature matrix is schematic: the full reader uses the mean-question and last-question paragraph attention from each of H selected heads, plus log paragraph token fraction and title mention (2H+2 features). The shown graph and composed answer are from a completed formal test example. No support annotations or answer labels are used at deployment.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default=str(ROOT/'paper/figures'));p.add_argument('--pdf',action='store_true');p.add_argument('--libreoffice',default='/tmp/coretrace-libreoffice/soffice');a=p.parse_args()
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    e=example();arts=[fig1(e),fig2(e),fig3(e)]
    combined=Presentation();combined.slide_width=Inches(W);combined.slide_height=Inches(H)
    for i,art in enumerate(arts,1):
        art.save(out/f'figure{i}.pptx')
        slide=combined.slides.add_slide(combined.slide_layouts[6])
        for sh in art.slide.shapes: slide.shapes._spTree.insert_element_before(deepcopy(sh.element),'p:extLst')
    combined.save(out/'figures1-3.pptx')
    (out/'captions.json').write_text(json.dumps(CAPTIONS,indent=2)+'\n')
    source=dict(source_id=e['source']['source_id'],model='Llama-3.1-8B-Instruct',seed=42,files=e['files'],example_selection='Both native constituent answers correct; composed native incorrect; composed final correct; ambiguous graph candidates.',reciprocal_example_quadruplet=e['quad']['quadruplet_id'],captions=CAPTIONS,style='Native PPT vectors; Liberation Serif (Times-compatible), muted blue/teal/orange; no embedded raster images.',mechanism_sources=['scripts/discover.py','scripts/causal.py','scripts/factorized_causal.py','scripts/necessity.py','scripts/content_causal.py','coretrace/method/pipeline.py','coretrace/method/text_selector.py','coretrace/models/scoped_rollback.py'],schematic_elements='Head ranking grid, feature matrix and attention bars are conceptual, not synthetic empirical results.')
    (out/'figure_sources.json').write_text(json.dumps(source,indent=2)+'\n')
    if a.pdf:
        exe=a.libreoffice or shutil.which('soffice')
        for stem in ['figure1','figure2','figure3','figures1-3']:
            subprocess.run([exe,'--headless','--convert-to','pdf','--outdir',str(out),str(out/f'{stem}.pptx')],check=True)
            if stem!='figures1-3':subprocess.run(['pdftoppm','-png','-scale-to','2000','-singlefile',str(out/f'{stem}.pdf'),str(out/stem)],check=True)
    print(f'Wrote {len(arts)} editable vector figures to {out}')

if __name__=='__main__':main()
