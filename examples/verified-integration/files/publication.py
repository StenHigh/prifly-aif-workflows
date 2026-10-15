"""Reference GitLab adapter algorithm. A project supplies the actual API client.

No network, credentials or glab executable are selected by this module. Its
offline fixtures model glab 1.119.0 --draft and writes with lost acknowledgements.
"""
import hashlib


def body_digest(body):
    return 'sha256:' + hashlib.sha256(body.encode()).hexdigest()


def draft_stem(title):
    stem = title.removeprefix('Draft: ')
    if stem.startswith('Draft: '):
        raise ValueError('More than one prepared Draft prefix: reconcile before publishing')
    return stem


def receipt(spec, status, reason='', mr=None, observed_target=None):
    return {'status': status, 'reason': reason, 'identity': spec['identity'],
            'candidate_commit': spec['candidate_commit'], 'target_commit': spec['target_commit'],
            'handoff_digest': spec['handoff_digest'], 'url': mr['url'] if mr else None,
            'observed_target_commit': observed_target,
            'body_digest': body_digest(mr['body']) if mr else None,
            'revision': mr['revision'] if mr else None}


def compatible(mr, spec):
    return all(mr[k] == spec[k] for k in ('identity', 'candidate_commit', 'target_commit', 'source_branch', 'target_branch'))


def publish(client, spec):
    """Inspect first; create one Draft or reuse the same owned publication.

    The API client must implement exact project/branch lookup, source ref CAS,
    read-after-write and revision-conditional title repair. Existing human text
    is never overwritten. A return value is evidence, not merge permission.
    """
    try:
        stem = draft_stem(spec['title'])
        state = client.inspect(spec)
        if state['target_commit'] != spec['target_commit']:
            return receipt(spec, 'reconcile_required', 'External target moved', observed_target=state['target_commit'])
        if len(state['mrs']) > 1:
            return receipt(spec, 'reconcile_required', 'Ambiguous existing publications; no write')
        if state['mrs']:
            mr = state['mrs'][0]
            if not compatible(mr, spec):
                return receipt(spec, 'reconcile_required', 'Existing MR belongs to different work; preserve it', mr)
            if mr['title'].startswith('Draft: Draft: ') or not mr['title'].startswith('Draft: '):
                return receipt(spec, 'reconcile_required', 'MR exists; formatting needs an addressed owner repair', mr, state['target_commit'])
            return receipt(spec, 'reused', mr=mr, observed_target=state['target_commit'])
        branch = state['source_branch']
        if branch is not None and (branch['identity'] != spec['identity'] or branch['commit'] != spec['candidate_commit']):
            return receipt(spec, 'reconcile_required', 'Source branch is foreign or changed; no overwrite')
        client.ensure_source_branch(spec, None if branch is None else branch['commit'])
        # With --draft, glab owns the prefix. Supply the title without it.
        mr = client.create(spec, title=stem, draft=True)
        after = client.inspect(spec)
        if after['target_commit'] != spec['target_commit']:
            return receipt(spec, 'reconcile_required', 'MR exists but external target moved after creation', mr, after['target_commit'])
        if not compatible(mr, spec) or mr['title'] != 'Draft: ' + stem:
            return receipt(spec, 'reconcile_required', 'MR exists; post-write identity/format validation failed', mr, after['target_commit'])
        return receipt(spec, 'created', mr=mr, observed_target=after['target_commit'])
    except (OSError, TimeoutError, ValueError, KeyError) as error:
        # An error is not proof of no write. Only inspect, never create again.
        try:
            observed = client.inspect(spec)
            matches = [mr for mr in observed['mrs'] if compatible(mr, spec)]
            if len(matches) == 1:
                mr = matches[0]
                if observed['target_commit'] == spec['target_commit'] and mr['title'] == 'Draft: ' + draft_stem(spec['title']):
                    return receipt(spec, 'reused', 'Write acknowledgement lost; existing MR inspected', mr, observed['target_commit'])
                return receipt(spec, 'reconcile_required', 'MR exists; inspect before an addressed repair', mr, observed['target_commit'])
        except (OSError, TimeoutError, ValueError, KeyError):
            pass
        return receipt(spec, 'reconcile_required', 'Publication outcome unknown; no blind retry: ' + str(error))


def repair_owned_title(client, spec, previous):
    """Explicit reconciliation of a recorded post-write formatting defect."""
    state = client.inspect(spec)
    if state['target_commit'] != spec['target_commit'] or len(state['mrs']) != 1:
        return receipt(spec, 'reconcile_required', 'Target/lookup changed; no repair')
    mr = state['mrs'][0]
    if previous['revision'] is None or previous['body_digest'] is None or previous['url'] is None:
        return receipt(spec, 'reconcile_required', 'Recorded revision/body identity unavailable; no unconditional title update', mr, state['target_commit'])
    if not compatible(mr, spec) or mr['url'] != previous['url'] or mr['revision'] != previous['revision'] or body_digest(mr['body']) != previous['body_digest']:
        return receipt(spec, 'reconcile_required', 'Foreign or intervening human edit; preserve it', mr)
    stem = spec['title']
    while stem.startswith('Draft: '):
        stem = stem.removeprefix('Draft: ')
    client.update_title(mr['url'], 'Draft: ' + stem, expected_revision=mr['revision'])
    return publish(client, {**spec, 'title': 'Draft: ' + stem})
