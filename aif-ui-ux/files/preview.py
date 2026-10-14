"""Read-only review of the exact JSON input before native Pri-Fly prepare."""
import argparse
import json
from pathlib import Path
import product

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--configuration',type=Path,required=True)
args=parser.parse_args()
raw=args.configuration.read_bytes();config=json.loads(raw);product.configuration(config)
requests={lens:product.project(config,lens) for lens in product.LENSES}
print(json.dumps({'configuration_digest':product.w1.digest(raw),'surface':config['surface'],
    'scope_reason':config['scope_reason'],'environment':config['environment'],
    'requests':requests,'scenarios':config['scenarios']},indent=2))
