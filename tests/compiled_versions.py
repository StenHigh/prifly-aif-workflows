#!/usr/bin/env python3
"""Refuse different compiled bytes under one kind/id/version across a release.

Compile the previous tag and the working tree with the same released binary,
host stubs and default owner configuration. No Run or shipping package import.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

import yaml

from verify import ROOT, PACKAGES, HOSTS, compile_package, forget_authority, prepare_repository, run


def git(repository, *arguments):
    return subprocess.run(["git", "-C", str(repository), *arguments], check=True,
                          capture_output=True, text=True, timeout=60).stdout.strip()


def previous_release(repository):
    # A tag build must compare with the preceding release, not with itself.
    tags = git(repository, "tag", "--points-at", "HEAD").splitlines()
    revision = "HEAD^" if any(re.fullmatch(r"v\d+\.\d+\.\d+", tag) for tag in tags) else "HEAD"
    tag = git(repository, "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*", "--exclude", "v*-*", revision)
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError(f"Expected a stable release tag, got {tag!r}; specify --baseline")
    return tag


def fingerprint(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def read_components(result, output, label):
    records = []
    for component in result["components"]:
        raw = (output / component["path"]).read_bytes()
        ref = component["ref"]
        if fingerprint(raw) != ref["digest"]:
            raise ValueError(f"{label}: {component['path']} differs from the compiler digest")
        # Contexts are raw media, not JSON definitions. Their ref carries identity.
        if component["kind"] in ("workflow", "step"):
            document = json.loads(raw)
            if (document["id"], document["version"]) != (ref["id"], ref["version"]):
                raise ValueError(f"{label}: document identity differs from compiler ref: {ref}")
        records.append({"kind": component["kind"], **ref, "source": label})
    if not records:
        raise ValueError(f"{label}: no compiled components were measured")
    return records


def check_collisions(records):
    """Use compiler digests, never a version/build key as a substitute for bytes."""
    seen = {}
    if not records:
        raise ValueError("No compiled components were measured")
    for record in records:
        key = record["kind"], record["id"], record["version"]
        previous = seen.get(key)
        if previous is not None and previous["digest"] != record["digest"]:
            raise ValueError(
                f"compiled_definition_drift: {key[0]} {key[1]}@{key[2]}: "
                f"{previous['source']} {previous['digest']} != {record['source']} {record['digest']}")
        seen[key] = record
    return len(seen)


def matrix(source):
    for package in PACKAGES:
        manifest = yaml.safe_load((source / package / "workflow.yaml").read_text())
        profiles = manifest["package"].get("profiles", {}).get("values", {})
        for host in HOSTS:
            for profile in profiles or (None,):
                yield package, host, profile


def source_digest(source):
    entries = {}
    for directory in (*PACKAGES, "contracts"):
        for path in sorted((source / directory).rglob("*")):
            if path.is_file():
                entries[str(path.relative_to(source))] = fingerprint(path.read_bytes())
    return fingerprint(json.dumps(entries, sort_keys=True).encode())


def compile_release(binary, source, root, label):
    root.mkdir()
    authority = root / "authority"
    try:
        repository, _ = prepare_repository(binary, root, source_root=source)
        before = run(binary, "--project", authority, "package", "list")
        records, builds = [], []
        for index, (package, host, profile) in enumerate(matrix(source)):
            output = root / f"build-{index}"
            result, _ = compile_package(binary, authority, repository, package, output, host, profile)
            name = f"{label}/{package}/{host}/{profile or 'default'}"
            components = read_components(result, output, name)
            records.extend(components)
            builds.append({"package": package, "host": host, "profile": profile,
                           "build_key": result["build_key"], "components": len(components)})
        if run(binary, "--project", authority, "package", "list") != before:
            raise ValueError(f"{label}: compile changed package trust")
        return records, builds
    finally:
        removed = forget_authority(authority)
        if removed != 1:
            raise ValueError(f"{label}: expected one registry entry, removed {removed}")


def dependency_regression(binary, root):
    """Leave the step YAML/version unchanged; change one resolved dependency."""
    root.mkdir()
    authority = root / "authority"
    try:
        repository, _ = prepare_repository(binary, root)
        package = repository / ".prifly/workflows/aif-classic"
        step = package / "steps/plan.yaml"
        original_step = step.read_bytes()
        records, cases, documents = [], [], {}
        for name, dependency in (("unchanged", None), ("repeat", None),
                                 ("instructions", "contexts/aif-plan-bridge.yaml"),
                                 ("schema", "schemas/task.yaml")):
            path = package / dependency if dependency else None
            original = path.read_bytes() if path else None
            try:
                if path:
                    text = original.decode()
                    if name == "instructions":
                        text += "\n  Dependency-only regression fixture.\n"
                    else:
                        text = text.replace("maxLength: 400}", "maxLength: 401}", 1)
                    if text.encode() == original:
                        raise ValueError(f"{name}: fixture did not change its dependency")
                    path.write_text(text)
                output = root / name
                result, docs = compile_package(binary, authority, repository, "aif-classic", output)
                compiled = read_components(result, output, f"dependency/{name}")
                records.extend(compiled)
                selected = next(record for record in compiled if record["id"] == "aif:step/plan")
                documents[name] = docs["aif:step/plan"]
                cases.append({"case": name, "step": selected})
                if step.read_bytes() != original_step:
                    raise ValueError("The regression fixture changed the step source")
            finally:
                if path:
                    path.write_bytes(original)
        baseline = cases[0]["step"]
        if cases[1]["step"]["digest"] != baseline["digest"] or cases[1]["step"]["version"] != baseline["version"]:
            raise ValueError("Identical compilation inputs did not reproduce the same step")
        for case, ref_path in ((cases[2], "instructions_ref"), (cases[3], "inputs")):
            other = case["step"]
            if documents[case["case"]][ref_path] == documents["unchanged"][ref_path]:
                raise ValueError(f"{case['case']}: the resolved dependency did not change")
            if other["digest"] == baseline["digest"] or other["version"] == baseline["version"]:
                raise ValueError(f"{case['case']}: dependency changed without a new step version/digest")
        check_collisions(records)
        return {"step_source_sha256": fingerprint(original_step),
                "author_step_version": yaml.safe_load(original_step)["version"],
                "cases": cases}
    finally:
        removed = forget_authority(authority)
        if removed != 1:
            raise ValueError(f"dependency fixture: expected one registry entry, removed {removed}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--baseline", help="Previous stable repository release tag; default: nearest preceding stable tag")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    baseline = args.baseline or previous_release(ROOT)
    # Resolve before archive; never interpolate a ref into a shell command.
    commit = git(ROOT, "rev-parse", "--verify", f"{baseline}^{{commit}}")
    with tempfile.TemporaryDirectory(prefix="aif-compiled-versions-") as temporary:
        root = Path(temporary)
        source = root / "released-source"
        source.mkdir()
        archive = root / "release.tar"
        subprocess.run(["git", "-C", str(ROOT), "archive", "--output", str(archive), commit], check=True, timeout=60)
        subprocess.run(["tar", "-xf", str(archive), "-C", str(source)], check=True, timeout=60)
        old, old_builds = compile_release(binary, source, root / "released", baseline)
        new, new_builds = compile_release(binary, ROOT, root / "candidate", "working-tree")
        identities = check_collisions(old + new)
        regression = dependency_regression(binary, root / "dependencies")
        report = {"outcome": "passed", "prifly": run(binary, "version")["version"],
                  "binary_sha256": fingerprint(binary.read_bytes()),
                  "baseline": {"tag": baseline, "commit": commit, "source_digest": source_digest(source), "builds": old_builds},
                  "candidate": {"head": git(ROOT, "rev-parse", "HEAD"), "source_digest": source_digest(ROOT), "builds": new_builds},
                  "components_read": len(old) + len(new), "unique_identities": identities,
                  "dependency_regression": regression, "registry_entries_removed": 3}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ("baseline", "candidate", "dependency_regression")}))


if __name__ == "__main__":
    main()
