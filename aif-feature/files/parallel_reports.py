"""Exact native manifest/report transport. No authority access or model decisions."""
import base64
import binascii
import json
import evidence as w1

READERS = ('security', 'review')
MAX_REPORT_BYTES = 4 * 1024 * 1024


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise w1.Invalid('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(w1.Invalid('Nonfinite JSON number')))


def report_refs(manifest):
    if not isinstance(manifest, dict):
        raise w1.Invalid('Expected native manifest object')
    if manifest.get('schema_version') != '1' or manifest.get('join_result') != 'satisfied':
        raise w1.Invalid('Parallel review did not satisfy all-join')
    rows = manifest.get('branches')
    if (not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows)
            or [r.get('id') for r in rows] != list(READERS)):
        raise w1.Invalid('Missing, duplicate, reordered or unknown reader branch')
    if manifest.get('selected_branch_ids') != list(READERS):
        raise w1.Invalid('Parallel selection does not include every reader')
    refs = {}
    for row in rows:
        if row.get('status') != 'completed' or row.get('outcome') != 'succeeded' or row.get('has_waivers') is not False:
            raise w1.Invalid('Reader not completed or accepted with a waiver')
        outputs = row.get('output_refs')
        if not isinstance(outputs, dict) or set(outputs) != {'report'}:
            raise w1.Invalid('Missing or unexpected reader output')
        ref = outputs['report']
        w1.obj(ref, ('artifact_id', 'revision', 'digest'), 'report ref')
        if (not isinstance(ref['artifact_id'], str) or not ref['artifact_id'].startswith('artifact:')
                or type(ref['revision']) is not int or ref['revision'] < 1
                or not isinstance(ref['digest'], str) or not w1.DIGEST.fullmatch(ref['digest'])):
            raise w1.Invalid('Invalid sealed report ref')
        refs[row['id']] = ref
    if len({(r['artifact_id'], r['revision']) for r in refs.values()}) != len(READERS):
        raise w1.Invalid('Readers cannot share the same report artifact')
    return refs


def unavailable(manifest_digest, reason):
    return {'schema_version': '1', 'manifest_digest': manifest_digest,
            'status': 'unavailable', 'reason': str(reason)[:4000], 'reports': []}


def unpack(manifest, manifest_digest, bundle):
    """Verify original bytes against exact refs, then leave W1 to assess reports."""
    refs = report_refs(manifest)
    w1.obj(bundle, ('schema_version', 'manifest_digest', 'status', 'reason', 'reports'), 'report bundle')
    if bundle['schema_version'] != '1' or bundle['manifest_digest'] != manifest_digest:
        raise w1.Invalid('Bundle belongs to another manifest')
    if bundle['status'] != 'ready' or bundle['reason'] != '':
        raise w1.Invalid('Sealed reports unavailable: ' + str(bundle['reason']))
    entries = bundle['reports']
    if (not isinstance(entries, list) or any(not isinstance(r, dict) for r in entries)
            or [r.get('branch') for r in entries] != list(READERS)):
        raise w1.Invalid('Bundle must contain every reader exactly once in sealed order')
    reports = {}
    for entry in entries:
        w1.obj(entry, ('branch', 'ref', 'raw_base64'), 'bundle report')
        if entry['ref'] != refs[entry['branch']]:
            raise w1.Invalid('Bundle substituted a sealed report ref')
        encoded = entry['raw_base64']
        if not isinstance(encoded, str) or len(encoded) > 4 * ((MAX_REPORT_BYTES + 2) // 3):
            raise w1.Invalid('Report exceeds the declared transport bound')
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise w1.Invalid('Invalid report base64') from error
        if len(raw) > MAX_REPORT_BYTES or base64.b64encode(raw).decode('ascii') != encoded:
            raise w1.Invalid('Noncanonical or oversized report encoding')
        if w1.digest(raw) != entry['ref']['digest']:
            raise w1.Invalid('Report bytes differ from sealed digest')
        reports[entry['branch']] = strict_json(raw)
    return reports
