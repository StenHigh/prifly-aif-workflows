#!/usr/bin/env python3
"""Install reviewed project-owned W6 additions. Never edits upstream workflow.yaml."""
import argparse
import hashlib
import importlib.util
import sys
import json
import os
import re
from pathlib import Path
import tempfile

try:
    import yaml
except ImportError:
    raise SystemExit(
        "Installer needs PyYAML6+: install examples/review-uiux-extensions/requirements.txt in a venv; workers use stdlib only."
    )

HERE = Path(__file__).resolve().parent


# Core uses YAML1.2: `on`, `off`, `yes`, `no` are strings, not booleans.
class Loader(yaml.SafeLoader):
    pass


Loader.yaml_implicit_resolvers = {
    k: [(tag, pattern) for tag, pattern in values if tag != "tag:yaml.org,2002:bool"]
    for k, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
Loader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$", re.I), list("tTfF")
)


def load(text):
    return yaml.load(text, Loader=Loader)


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode() + b"\n"
    )


def validate_configuration(settings, mode):
    manifest = json.loads((HERE / "bundle/manifest.json").read_text())
    modules = []
    for name in ("evidence", "product"):
        path = HERE / "bundle/project/files" / ("w6-" + name + ".py")
        if (
            digest(path.read_bytes())
            != manifest["files"][str(path.relative_to(HERE / "bundle"))]
        ):
            raise ValueError("Validator source drift")
        spec = importlib.util.spec_from_file_location("w6_validate_" + name, path)
        module = importlib.util.module_from_spec(spec)
        previous = sys.modules.get("evidence")
        try:
            if modules:
                sys.modules["evidence"] = modules[0]
            spec.loader.exec_module(module)
        finally:
            if previous is None:
                sys.modules.pop("evidence", None)
            else:
                sys.modules["evidence"] = previous
        modules.append(module)
    if mode in ("review", "combined"):
        modules[0].request(settings["review"])
    elif settings["review"] is not None:
        raise ValueError("UIUX mode requires review:null")
    if mode in ("uiux", "combined"):
        modules[1].configuration(settings["product"])
        if settings["product"]["environment"]["shared_resource"] is not None:
            raise ValueError(
                "Initial W6 recipes qualify isolated owned environments only; shared_resource must be null"
            )
    elif settings["product"] is not None:
        raise ValueError("Review mode requires product:null")


def plan(
    repository, package, configuration, mode, after, before, failure, finish, port
):
    repository = repository.resolve(strict=True)
    folder = repository / ".prifly/workflows" / package
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Expected an installed workflow folder")
    profile = repository / ".prifly/project.yaml"
    root = folder / "workflow.yaml"
    extend = folder / "extend.yaml"
    for p in (profile, root, extend, configuration):
        if p.is_symlink() or not p.is_file():
            raise ValueError("Expected regular reviewed file: " + str(p))
    upstream = load(root.read_text())
    settings = json.loads(configuration.read_text())
    if settings.get("mode") != mode or set(settings) != {"mode", "review", "product"}:
        raise ValueError("Configuration must declare exact mode/review/product")
    validate_configuration(settings, mode)
    stages = upstream["stages"]
    if not all(s in stages for s in (after, before, failure, finish)):
        raise ValueError("Unknown root placement/finish stage")
    if before not in stages[after].get("on", {}).values():
        raise ValueError("after→before must be a direct on route")
    if finish not in stages[before].get("on", {}).values():
        raise ValueError("commit→finish must be a direct on route")
    if (
        stages[failure].get("kind") != "finish"
        or stages[failure].get("outcome") == "succeeded"
    ):
        raise ValueError("Failure target must be an unsuccessful finish")
    if stages[before].get("kind") != "step":
        raise ValueError("Before must be the actual commit step")
    existing = load(extend.read_text()) or {}
    project = load(profile.read_text())
    if project.get("schema_version") not in (
        "prifly-project-profile/2",
        "prifly-project-profile/3",
        "prifly-project-profile/4",
    ):
        raise ValueError("Project profile/2, /3 or /4 required")
    existing.setdefault("extensions", [])
    refs = existing.setdefault("references", {})
    programs = existing.setdefault("execution_bindings", {}).setdefault("steps", {})
    if any(e.get("id", "").startswith("w6-") for e in existing["extensions"]):
        raise ValueError(
            "W6 already installed; remove reviewed W6 overlay before reinstalling; no silent upgrade"
        )
    manifest = json.loads((HERE / "bundle/manifest.json").read_text())
    selected = manifest["modes"][mode]
    for name in manifest["references"]:
        if name in refs or name in upstream["package"].get("references", {}):
            raise ValueError("Reference alias conflict: " + name)
    if set(programs) & set(selected["bindings"]):
        raise ValueError("Execution binding conflict")
    changes = {}
    for relative in selected["files"]:
        source = HERE / "bundle" / relative
        raw = source.read_bytes()
        if digest(raw) != manifest["files"][relative]:
            raise ValueError("Bundle source drift: " + relative)
        target = folder / relative
        if target.exists() or target.is_symlink():
            raise ValueError("Project file already exists: " + relative)
        if any(
            parent.is_symlink()
            for parent in target.parents
            if parent != repository.parent
        ):
            raise ValueError("Project path traverses symlink")
        changes[target] = raw
    for name in ("w6-settings.json", "w6-provenance.json"):
        target = folder / "project/files" / name
        if target.exists() or target.is_symlink():
            raise ValueError(
                "Project file already exists: " + str(target.relative_to(folder))
            )
    changes[folder / "project/files/w6-settings.json"] = encoded(settings)
    short = upstream["id"].rsplit("/", 1)[-1]
    existing["authoring"] = "prifly-extension/2"
    refs.update(manifest["references"])
    programs.update(selected["bindings"])
    existing["extensions"] += [
        {
            "id": "w6-quality",
            "workflow": short,
            "call": selected["call"],
            "between": {"from": after, "to": before},
            "input_bindings": {"implementation": f"$stages.{after}.{port}"},
            "on": {"succeeded": before, "partial": failure, "rejected": failure},
            "on_error": failure,
        },
        {
            "id": "w6-committed-quality",
            "workflow": short,
            "call": "w6-committed",
            "between": {"from": before, "to": finish},
            "input_bindings": {
                "implementation": f"$stages.{before}.{port}",
                "receipt": "$stages.w6-quality.receipt",
            },
            "on": {"succeeded": finish, "rejected": failure},
            "on_error": failure,
        },
    ]
    project["schema_version"] = (
        "prifly-project-profile/3"
        if project["schema_version"] == "prifly-project-profile/2"
        else project["schema_version"]
    )
    changes[extend] = encoded(existing)
    changes[profile] = encoded(project)
    # Before/after hashes fence accidental edits between preview and apply.
    before_hash = {
        str(p.relative_to(repository)): digest(p.read_bytes()) if p.exists() else None
        for p in changes
    }
    changes[folder / "project/files/w6-provenance.json"] = encoded(
        {
            "protocol": "w6-project-install/1",
            "mode": mode,
            "upstream_workflow_sha256": digest(root.read_bytes()),
            "sources": manifest["sources"],
            "bundle_version": manifest["version"],
        }
    )
    before_hash[
        str((folder / "project/files/w6-provenance.json").relative_to(repository))
    ] = None
    summary = {
        "protocol": "w6-install-plan/1",
        "mode": mode,
        "package": package,
        "upstream_workflow_sha256": digest(root.read_bytes()),
        "before": before_hash,
        "after": {
            str(p.relative_to(repository)): digest(raw) for p, raw in changes.items()
        },
        "project_profile": project["schema_version"],
        "extensions": existing["extensions"][-2:],
    }
    return summary, changes


def apply(repository, summary, changes):
    folder = repository / ".prifly/workflows" / summary["package"]
    if (
        digest((folder / "workflow.yaml").read_bytes())
        != summary["upstream_workflow_sha256"]
    ):
        raise ValueError("Upstream root changed after preview")
    written = []
    backup = Path(tempfile.mkdtemp(prefix="w6-project-backup-"))
    try:
        for path, raw in changes.items():
            relative = str(path.relative_to(repository))
            old = path.read_bytes() if path.exists() else None
            expected = summary["before"][relative]
            if (digest(old) if old is not None else None) != expected:
                raise ValueError("Project changed after preview: " + relative)
            if old is not None:
                copy = backup / relative
                copy.parent.mkdir(parents=True, exist_ok=True)
                copy.write_bytes(old)
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=path.parent, prefix=".w6-stage-", delete=False
            ) as stream:
                stream.write(raw)
                temp = Path(stream.name)
            os.replace(temp, path)
            written.append((path, old, raw))
    except BaseException:
        for path, old, ours in reversed(written):
            if path.read_bytes() != ours:
                continue  # Never overwrite a concurrent owner edit.
            if old is None:
                path.unlink()
            else:
                path.write_bytes(old)
        raise
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--package", default="aif-classic")
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--mode", choices=["review", "uiux", "combined"], required=True)
    for name, default in [
        ("after", "review"),
        ("before", "commit"),
        ("failure", "abandoned"),
        ("finish", "done"),
        ("implementation-port", "implementation"),
    ]:
        parser.add_argument("--" + name, default=default)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-plan-digest")
    args = parser.parse_args()
    if not args.package or "/" in args.package or args.package in (".", ".."):
        parser.error("package is one installed folder name")
    try:
        summary, changes = plan(
            args.repository,
            args.package,
            args.configuration,
            args.mode,
            args.after,
            args.before,
            args.failure,
            args.finish,
            args.implementation_port,
        )
        identity = digest(encoded(summary))
        result = {**summary, "review_digest": identity, "applied": False}
        if args.apply:
            if args.expected_plan_digest != identity:
                raise ValueError(
                    "Review digest changed/missing; prepare again with the same arguments"
                )
            result["backup_directory"] = str(
                apply(args.repository.resolve(), summary, changes)
            )
            result["applied"] = True
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, yaml.YAMLError) as error:
        parser.exit(1, "W6 installation refused: " + str(error) + "\n")


if __name__ == "__main__":
    main()
