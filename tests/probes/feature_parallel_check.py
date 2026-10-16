#!/usr/bin/env python3
"""Whole aif-feature parallel composition, not the old W5 qualification graph."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from feature_check import run_case
import verify

CASES = {
    'backend': ('backend', None),
    'repair-checks': ('repair-checks', None),
    'repair-security': ('repair-security', None),
    'repair-review': ('repair-review', None),
    'required-unavailable': ('required-unavailable', None),
    'owner-stop': ('owner-stop', None),
    'last-round': ('exhaustion', None),
    'max-budget': ('max-budget', None),
    'cancel-after-first': ('cancel-resume', None),
    'cancel-after-edit': ('cancel-resume', 'during-reader-edit'),
    'timeout-replay': ('cancel-resume', 'timeout'),
    'one-timeout-replay': ('cancel-resume', 'one-timeout'),
    'partial-resume': ('blocked-resume', None),
    'commit-replay': ('commit-resume', None),
    'intervening-edit': ('stale-after-review', None),
    'frontend-refused': ('frontend', None),
    'unsupported-host': ('backend', 'unsupported-host'),
    **{name: ('backend', name) for name in ('bad-digest', 'missing-report', 'stale-bundle', 'export-unavailable',
                                           'stale-report', 'shared-session', 'failed-unavailable')},
}


def main():
    if not __debug__: raise RuntimeError('Assertions are required')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--case', choices=CASES)
    selection.add_argument('--cases', choices=CASES, nargs='+', help='A named regression subset; default is the full matrix')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--live-skills', type=Path)
    parser.add_argument('--artifacts', type=Path)
    parser.add_argument('--jobs', type=int, choices=(1, 2, 3), default=1)
    args = parser.parse_args()
    if args.live_skills and (args.case != 'backend' or args.artifacts is None):
        parser.error('Live independent CLI readers require --case backend and --artifacts')
    if args.jobs != 1 and (args.case or args.live_skills):
        parser.error('--jobs is for the complete synthetic matrix only')
    if args.artifacts: args.artifacts.mkdir(parents=True, exist_ok=True)
    selected = [args.case] if args.case else args.cases or list(CASES)
    summary = {'prifly': verify.run(args.binary, 'version')['version'],
               'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
               'boundary': 'Whole shipping feature graph; actual public report export and deterministic aggregate. '
                           + ('Synthetic author/checks, actual fresh CLI security/review via shipped dispatcher.' if args.live_skills else
                              'Synthetic host reports/capability, not live independent sessions.'),
               'selected_cases': selected, 'cases': [], 'matrix_complete': False}
    def record(row):
        summary['cases'].append(row)
        args.report.write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps({'scenario': row['scenario'], 'outcome': row['outcome'], 'batches': len(row.get('parallel_batches', [])),
                          'cleaned': row['cleaned']}), flush=True)
    if args.jobs > 1:
        # Each subprocess gets a private HOME/registry, not merely a separate Run.
        # No live credentials or user monitor entries enter this synthetic path.
        with tempfile.TemporaryDirectory(prefix='w5-feature-matrix-') as tmp:
            def isolated(name):
                root = Path(tmp) / name
                fixture_home = root / 'home'; fixture_home.mkdir(parents=True)
                report_file = root / 'result.json'
                cmd = [sys.executable, '-B', str(Path(__file__).resolve()), '--binary', str(args.binary.resolve()),
                       '--case', name, '--report', str(report_file)]
                result = subprocess.run(cmd, capture_output=True, text=True,
                                        env={**os.environ, 'HOME': str(fixture_home), 'XDG_CONFIG_HOME': str(fixture_home / '.config')})
                if result.returncode:
                    raise AssertionError(name + ': ' + result.stdout + result.stderr)
                child = json.loads(report_file.read_text())
                assert child['matrix_complete'] and len(child['cases']) == 1
                return child['cases'][0]
            pool = ThreadPoolExecutor(max_workers=args.jobs)
            try:
                pending = [pool.submit(isolated, name) for name in selected]
                for future in as_completed(pending): record(future.result())
            finally:
                pool.shutdown(wait=True, cancel_futures=True)
    else:
        for name in selected:
            case, fault = CASES[name]
            row = run_case(args.binary, case, review_mode='parallel-backend', parallel_fault=fault,
                           parallel_live=bool(args.live_skills), skills=args.live_skills, artifacts=args.artifacts)
            if args.live_skills:
                observations = row['parallel_observations']
                assert len(observations) == 2 and len({o['session_id'] for o in observations}) == 2
                overlap = min(o['ended_monotonic'] for o in observations) - max(o['started_monotonic'] for o in observations)
                assert overlap > 0, 'Concurrent delivery did not demonstrate actual reader-turn overlap'
                row['reader_turn_overlap_seconds'] = overlap
            row['scenario'] = name
            record(row)
    summary['matrix_complete'] = True
    args.report.write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__': main()
