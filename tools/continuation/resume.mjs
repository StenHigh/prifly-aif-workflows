// The first step of a continuation tail: the work the CLI did before Pri-Fly
// 0.13.56, now a step whose result the Run records. The tail is handed the
// source Run's claimed tree as it was left, so this checks that the tree still
// holds the implementation the source accepted, and describes the tree as it is
// now — commits made since, and uncommitted files too, because the gates judge
// the tree and the commit step commits it.
//
// fail: the tree does not contain that implementation — another branch, a reset.
// blocked: nothing could be judged — no claimed tree, no git.
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const MAX_CHANGED_FILES = 1000; // aif-continuation:schema/implementation maxItems
const envelope = JSON.parse(readFileSync(0, 'utf8'));
const context = JSON.parse(readFileSync(process.env.PRIFLY_CONTEXT_FILE, 'utf8'));
const result = {
  schema_version: '1',
  run_id: envelope.run_id,
  step_instance_id: envelope.step_instance_id,
  attempt_id: envelope.attempt_id,
  envelope_digest: process.env.PRIFLY_ENVELOPE_DIGEST,
  verdict: 'pass', outputs: {}, evidence_refs: [], effect_receipt_refs: [], summary: '',
};

class Unrelated extends Error {}
class Unjudged extends Error {}

const repository = process.env.PRIFLY_REPOSITORY_WORKSPACE;
const git = (...args) => {
  try {
    return execFileSync('git', args, { cwd: repository, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  } catch (error) {
    if (error.code === 'ENOENT') throw new Unjudged('git is not on PATH (/usr/bin:/bin) for this program');
    throw error;
  }
};
const contains = (ancestor, head) => {
  try {
    git('merge-base', '--is-ancestor', ancestor, head);
    return true;
  } catch (error) {
    if (error instanceof Unjudged) throw error;
    if (error.status === 1) return false; // not an ancestor; 128 is an unknown commit
    throw new Unrelated(`${ancestor} is not a commit in this repository`);
  }
};
const paths = text => text.split('\0').filter(Boolean);

try {
  if (!repository) throw new Unjudged('no claimed repository workspace was handed to this step (PRIFLY_REPOSITORY_WORKSPACE is unset)');
  const previous = JSON.parse(readFileSync(context.inputs.previous_implementation.path, 'utf8'));
  const head = git('rev-parse', '--verify', 'HEAD^{commit}').trim();
  for (const commit of [previous.base_commit, previous.head_commit]) {
    if (!contains(commit, head)) {
      throw new Unrelated(`HEAD ${head} does not contain ${commit} from the source implementation; this tree is not a continuation of that Run`);
    }
  }
  // Against the working tree, not HEAD: what the gates read is the tree.
  const changed = new Set([
    ...paths(git('diff', '--name-only', '-z', '--no-renames', previous.base_commit)),
    ...paths(git('ls-files', '--others', '--exclude-standard', '-z')),
  ]);
  if (changed.size > MAX_CHANGED_FILES) {
    throw new Unrelated(`${changed.size} files changed since ${previous.base_commit}; the implementation schema carries at most ${MAX_CHANGED_FILES}`);
  }
  const implementation = { base_commit: previous.base_commit, head_commit: head, changed_files: [...changed].sort() };
  const slot = context.outputs.implementation;
  const bytes = Buffer.from(JSON.stringify(implementation));
  writeFileSync(slot.path, bytes);
  result.outputs.implementation = {
    artifact_id: slot.artifact_id, revision: slot.revision,
    digest: 'sha256:' + createHash('sha256').update(bytes).digest('hex'),
  };
  result.summary = `HEAD ${head} contains the source implementation; ${changed.size} file(s) changed since ${previous.base_commit}`;
} catch (error) {
  result.verdict = error instanceof Unrelated ? 'fail' : 'blocked';
  result.outputs = {};
  result.summary = error instanceof Unrelated || error instanceof Unjudged ? error.message : `git failed: ${error.message}`;
}
writeFileSync(3, JSON.stringify(result) + '\n');
