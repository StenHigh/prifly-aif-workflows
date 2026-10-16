#!/usr/bin/env python3
"""Render a test-audit example with an explicit local base commit; stdlib only."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path('.'))
    parser.add_argument('--base', required=True, help='Original task base: a local commit or ref')
    parser.add_argument('--template', choices=('python', 'node', 'monorepo'), required=True)
    parser.add_argument('--output', type=Path, required=True, help='New JSON file outside the target repository')
    parser.add_argument('--require-separate-session', action='store_true')
    args = parser.parse_args()
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0'}

    def git(*arguments):
        result = subprocess.run(['git', '-C', str(args.repository), *arguments], env=env,
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError('Repository/base must resolve locally; inspect the repository and --base')
        return result.stdout.strip()

    try:
        repository = Path(git('rev-parse', '--show-toplevel')).resolve(strict=True)
        base = git('rev-parse', '--verify', '--end-of-options', args.base + '^{commit}')
        if not re.fullmatch(r'[0-9a-f]{40}', base):
            raise ValueError('Expected a full SHA-1 base commit supported by git-candidate/1')
        output = args.output.resolve()
        try:
            output.relative_to(repository)
        except ValueError:
            pass
        else:
            raise ValueError('Write config outside the target repository to keep the candidate unchanged')
        template = Path(__file__).with_name(args.template + '.config.json')
        config = json.loads(template.read_text(encoding='utf-8'))
        config['base_commit'] = base
        config['require_separate_session'] = args.require_separate_session
        with output.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(config, indent=2) + '\n')
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    print(json.dumps({'config': str(output), 'base_commit': base, 'template': args.template}))


if __name__ == '__main__':
    main()
