"""Run one deterministic partition of the complete browser suite; omit no tests."""
import argparse
import json
from pathlib import Path
import pytest

parser=argparse.ArgumentParser()
parser.add_argument('--index',type=int,required=True)
parser.add_argument('--total',type=int,required=True)
parser.add_argument('--collect-only',action='store_true')
args=parser.parse_args()
if args.total<1 or not 0<=args.index<args.total:
    parser.error('index must be inside the positive shard count')

class Shard:
    def pytest_collection_modifyitems(self,config,items):
        all_items=list(items)
        selected=[item for index,item in enumerate(all_items) if index%args.total==args.index]
        deselected=[item for index,item in enumerate(all_items) if index%args.total!=args.index]
        config.hook.pytest_deselected(items=deselected)
        items[:]=selected
        out=Path('test-results');out.mkdir(exist_ok=True)
        (out/f'browser-shard-{args.index}.json').write_text(json.dumps({'index':args.index,'totalShards':args.total,'totalCollected':len(all_items),'selected':[item.nodeid for item in selected]},indent=2))
        print(f'Browser shard {args.index+1}/{args.total}: {len(selected)} of {len(all_items)} collected cases')

options=['-m','e2e','tests/e2e','-q']
if args.collect_only:options.append('--collect-only')
raise SystemExit(pytest.main(options,plugins=[Shard()]))
