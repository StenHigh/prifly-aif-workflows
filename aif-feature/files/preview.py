"""Read-only review of a W3 task's exact bytes and declared acceptance."""
import argparse
import json
from pathlib import Path
import feature

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--task',type=Path,required=True)
parser.add_argument('--profile',choices=('backend','frontend'),required=True)
args=parser.parse_args();raw=args.task.read_bytes();task=json.loads(raw)
feature.configuration(task,args.profile)
print(json.dumps({'task_digest':feature.w1.digest(raw),'profile':args.profile,'task':task},indent=2))
