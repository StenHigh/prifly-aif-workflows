#!/usr/bin/env python3
"""Write a new explicit feature task outside the target Git tree."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--consumer", choices=["minimal", "classic"], required=True)
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(
        subprocess.check_output(
            ["git", "-C", str(args.repository), "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
    ).resolve()
    output = args.output.resolve()
    if output.is_relative_to(repository):
        parser.error("Output must be outside the target Git tree")
    task = {"title": args.title, "description": args.description}
    if args.consumer == "minimal":
        task["base_commit"] = subprocess.check_output(
            [
                "git",
                "-C",
                str(repository),
                "rev-parse",
                "--verify",
                args.base + "^{commit}",
            ],
            text=True,
        ).strip()
    with output.open("x") as stream:
        json.dump(task, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(output)


if __name__ == "__main__":
    main()
