#!/usr/bin/env python3
"""Install the revision in a complete CoReTrace checkout; never push or edit model/data files."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='4edfa337e0b9c5cabec22128f2db25d8c8e4d17a'
OLD="The teaser uses a Llama example whose evidence states that Walter II of Avesnes is the son of James of Avesnes and that James was killed at the Battle of Arsuf. Native constituent answers identify James and Arsuf, whereas the native composed answer is ``Avesnes.'' The final procedure answers ``Arsuf.''"
NEW="The teaser uses the John Corvinus test case. All three models correctly identify Matthias Corvinus and John Hunyadi in the two constituent queries, but return Matthias Corvinus on the composed question. The complete procedure selects the bridge paragraph and answers John Hunyadi. The case illustrates composition repair, while the Angela case below isolates the joint-intervention behavior."

def run(*args, cwd=ROOT):
    subprocess.run(list(args),cwd=cwd,check=True)

def replace_once(s,old,new):
    if s.count(old)!=1: raise ValueError('Missing or nonunique integration anchor: '+old[:100])
    return s.replace(old,new,1)

def integrate():
    p=ROOT/'analysis/plot_results.py'; original=p.read_bytes();s=original.decode('utf8')
    block=(ROOT/'analysis/story_revision_plot.inc').read_text(encoding='utf8')
    if '# BEGIN STORY_REVISION_V5' in s or '# BEGIN STORY_REVISION_V4' in s:
        pattern=r"(?ms)^# BEGIN STORY_REVISION_V[45].*?^# END STORY_REVISION_V[45]\n*"
        if len(re.findall(pattern,s)) != 1:
            raise ValueError('Expected exactly one previous integrated story block')
        updated=re.sub(pattern,lambda _: block.rstrip()+'\n\n',s,count=1)
    else:
        digest=hashlib.sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()
        if digest!=BASE: raise ValueError(f'Unexpected original plot_results.py Git blob {digest}; expected {BASE}. Merge snippet manually if your checkout is newer.')
        updated=replace_once(s,'def main() -> None:',block+'\n\ndef main() -> None:')
        updated=replace_once(updated,'"mechanism_structure","composition_address"]','"mechanism_structure","composition_address","story_revision"]')
        updated=replace_once(updated,'"composition_address":make_composition_address}','"composition_address":make_composition_address,"story_revision":make_story_revision}')
    compile(updated,str(p),'exec')
    if updated!=s:
        p.write_text(updated,encoding='utf8')
        print('Integrated V5 story_revision into original plot_results.py')
    ap=ROOT/'paper/sections/appendix.tex'
    text=ap.read_text(encoding='utf8')
    if NEW not in text: ap.write_text(replace_once(text,OLD,NEW),encoding='utf8')
    run(sys.executable,'analysis/plot_results.py','--only','story_revision')

def build():
    paper=ROOT/'paper'; builddir=ROOT/'analysis/build_story_revision'
    run('bash','analysis/compile_paper.sh',str(paper),str(builddir))
    pdf=builddir/'main.pdf'; log=(builddir/'main.log').read_text(errors='replace')
    if re.search(r'undefined references|Citation .* undefined|Reference .* undefined|LaTeX Error|The page layout violates the ICML style',log,re.I): raise RuntimeError('Build has unresolved references or an ICML layout error. See '+str(builddir/'main.log'))
    pages=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True).split('\f')
    end=next((i+1 for i,p in enumerate(pages) if re.search(r'\b5\.?\s+Conclusion\b',p)),None)
    impact=next((i+1 for i,p in enumerate(pages) if 'Impact Statement' in p),None)
    if end!=8 or impact!=9: raise RuntimeError(f'Expected conclusion on page 8 and Impact Statement on page 9, found {end}, {impact}. Inspect compiled PDF before copying it to paper/.')
    shutil.copy2(pdf,paper/'main.pdf')
    if (builddir/'main.bbl').exists():shutil.copy2(builddir/'main.bbl',paper/'main.bbl')
    # Overleaf-ready original source, not the preview's retained PDF backmatter.
    archive=builddir/'CoReTrace_Overleaf_full.zip'
    allowed={'.tex','.bib','.bst','.sty','.cls','.pdf','.png','.jpg','.jpeg','.eps','.bbl'}
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(paper.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in allowed or any(x.startswith('.') for x in path.relative_to(paper).parts):continue
            if path.name=='main.pdf':continue
            z.write(path,path.relative_to(paper))
    print('Full compiled paper:',paper/'main.pdf');print('Full Overleaf source:',archive)
    print('Visually inspect all rendered pages before committing. No push was performed.')

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--compile',action='store_true');args=a.parse_args()
    if not (ROOT/'paper/sections/appendix.tex').exists() or not (ROOT/'paper/icml2027.sty').exists(): raise SystemExit('Apply this overlay to the complete original repository first.')
    integrate()
    if args.compile:build()
if __name__=='__main__':main()
