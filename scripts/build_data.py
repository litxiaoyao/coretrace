"""Rebuild the fixed CoRe-2Wiki data from the original public 2Wiki archive."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coretrace.data.builders.core2wiki import build

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True,type=Path,help='Original 2WikiMultiHopQA data_ids.zip')
    parser.add_argument('--output',required=True,type=Path,help='New output directory; existing data are never overwritten')
    args=parser.parse_args()
    print(json.dumps(build(args.archive,args.output),indent=2))

if __name__=='__main__':main()
