#!/usr/bin/env python3
"""Integrate final manuscript figures into the existing, single plotting entry."""
from pathlib import Path
import argparse, ast, subprocess, shutil, zipfile, re
ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'analysis'
P = ROOT / 'paper'
BEGIN = '# BEGIN CORETRACE_FINAL_MECHANISM:'
END = '# END CORETRACE_FINAL_MECHANISM'
ANCHOR = '# END STORY_REVISION_V5'
CALL = '        make_relation_population_revision()'
NEWCALL = '        make_final_mechanism_figures()'

def integrate(path, snippet):
    s = path.read_text(encoding='utf-8')
    if BEGIN in s:
        i = s.index(BEGIN); j = s.index(END, i) + len(END)
        s = s[:i] + snippet.rstrip() + s[j:]
    else:
        if s.count(ANCHOR) != 1 or s.count(CALL) != 1:
            raise RuntimeError(f'Unexpected V5 structure in {path}; do not overwrite manually.')
        s = s.replace(ANCHOR, snippet.rstrip()+'\n'+ANCHOR, 1)
    if NEWCALL not in s:
        if s.count(CALL) != 1: raise RuntimeError('Expected unique V5 plot-call anchor')
        s = s.replace(CALL, CALL+'\n'+NEWCALL, 1)
    if path.suffix == '.py': ast.parse(s)
    path.write_text(s, encoding='utf-8')

def run(*args): subprocess.run(args, cwd=ROOT, check=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--compile',action='store_true'); args=ap.parse_args()
    required=['data_revision_token_capture.json','data_revision_adapted_routing.csv','data_revision_relation_reading_summary.csv','data_revision_mechanism_repair.csv']
    for n in required:
        if not (A/'figure_data'/n).is_file(): raise RuntimeError('Missing pushed V5 result: '+n)
    snippet=(A/'final_mechanism_plot.inc').read_text(encoding='utf-8');ast.parse(snippet)
    integrate(A/'plot_results.py', snippet)
    # Keep V5's retained source fragment synchronized with the numerical entry.
    if (A/'story_revision_plot.inc').is_file(): integrate(A/'story_revision_plot.inc', snippet)
    run('python','analysis/plot_results.py','--only','story_revision')
    for n in ('data_main_relation_tokens_final','data_main_mechanism_closure_final','data_main_address_signal_final'):
        for ext in ('pdf','png'):
            f=P/'figures'/f'{n}.{ext}'
            if not f.is_file() or not f.stat().st_size: raise RuntimeError('Missing measured plot: '+str(f))
    if not args.compile: return
    build=A/'build_final_mechanism'
    run('bash','analysis/compile_paper.sh','paper',str(build))
    log=(build/'main.log').read_text(errors='replace');
    if re.search(r'Overfull \\[hv]box|There were undefined|Citation .+ undefined|Reference .+ undefined|LaTeX Error|Fatal error',log,re.I):
        raise RuntimeError('Review compile warnings/errors before replacing main.pdf')
    p8=subprocess.check_output(['pdftotext','-f','8','-l','8',str(build/'main.pdf'),'-'],text=True)
    p9=subprocess.check_output(['pdftotext','-f','9','-l','9',str(build/'main.pdf'),'-'],text=True)
    p10=subprocess.check_output(['pdftotext','-f','1','-l','8',str(build/'main.pdf'),'-'],text=True)
    # Structural checks only; this is not a visual review of the official PDF.
    if 'Conclusion' not in p8 or 'Impact Statement' not in p9 or '??' in p10:
        raise RuntimeError('Official build does not satisfy eight-page body/reference check; keep the previous PDF and report the log.')
    captions = set(int(x) for x in re.findall(r'\bFigure\s+(\d+)\.', p10))
    if captions != set(range(1, 14)):
        raise RuntimeError(f'Expected main Figure 1-13, found {sorted(captions)}; keep the previous PDF and report the log.')
    shutil.copy2(build/'main.pdf',P/'main.pdf')
    if (build/'main.bbl').exists(): shutil.copy2(build/'main.bbl',P/'main.bbl')
    # Package source, not old PDF or build outputs.
    allowed={'.tex','.bib','.sty','.bst','.cls','.clo','.def','.cfg','.fd','.pdf','.png','.jpg','.jpeg','.eps','.svg','.bbl'}
    zpath=build/'CoReTrace_Overleaf_full.zip'
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(P.rglob('*')):
            rel=f.relative_to(P)
            if f.is_file() and f.suffix.lower() in allowed and not any(p.startswith('.') for p in rel.parts) and not (len(rel.parts)==1 and f.suffix.lower() in {'.pdf','.png','.jpg','.jpeg'}):
                z.write(f,rel.as_posix())
    with zipfile.ZipFile(zpath) as z: assert z.testzip() is None
    print('Official build passed automated structure/reference checks. PDF and bibliography synchronized; Overleaf:',zpath)
if __name__=='__main__':main()
