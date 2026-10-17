"""Supplemental controlled-host cancellation/cleanup/continue qualification.

Runs existing recipes unchanged. Adds one scenario to the synthetic controller
in memory; no canonical package, engine, or repository probe bytes are edited.
"""
import json
from pathlib import Path
import sys
import types
from concurrent.futures import ProcessPoolExecutor

path = Path('tests/probes/call_review_check.py').resolve()
source = path.read_text()
assert source.count('("resume", "commit-resume")') == 2
source = source.replace('("resume", "commit-resume")', '("resume", "commit-resume", "cancel-resume")')
source = source.replace('if scenario == "cancel":', 'if scenario == "cancel" or scenario == "cancel-resume" and iteration == 0:')
source = source.replace('if scenario == "cancel" and kind == "ui":', 'if (scenario == "cancel" or scenario == "cancel-resume" and iteration == 0) and kind == "ui":')
source = source.replace('for turn in range(60):', 'cancelled = False\n                for turn in range(60):')
source = source.replace('assert state["outcome"] == "rejected" and not commits, state', 'assert state["outcome"] == (None if scenario == "cancel-resume" else "rejected") and not commits, state\n                    if environment:\n                        environment.close()  # Controlled operator: exact owned owner/session.')
source = source.replace('("pass", "resume", "commit-resume")', '("pass", "resume", "commit-resume", "cancel-resume")')
module = types.ModuleType('w6_cancel_continue')
module.__file__ = str(path)
exec(compile(source, str(path), 'exec'), module.__dict__)


def run(args):
    result = module.case(*args)
    result['operator_cleanup_before_continue'] = True
    print(json.dumps({k:v for k,v in result.items() if k not in ('evidence','live_sessions')}), flush=True)
    return result


if __name__ == '__main__':
    binary = Path('/tmp/aif-prifly-01380/prifly')
    cases = [(binary, 'review', 'minimal', 'cancel-resume', None, 'codex-cli'),
             (binary, 'uiux', 'classic', 'cancel-resume', None, 'codex-cli')]
    with ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run, cases))
    Path('/tmp/aif-w6-cancel-continue80.json').write_text(json.dumps(results, indent=2)+'\n')
