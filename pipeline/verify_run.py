#!/usr/bin/env python3
"""Check that a translation JSON still matches its recorded generation run."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="The generated JSON file")
    args = parser.parse_args()
    output = args.output
    metrics_file = output.with_suffix(".metrics.json")
    if not output.exists() or not metrics_file.exists():
        raise SystemExit("Generated JSON or matching metrics file is missing")
    metrics = json.loads(metrics_file.read_text())
    prompt_file = output.parent / metrics["prompt_file"]
    expected_prompt = metrics["prompt_sha256"]
    expected_output = metrics["output_sha256"]
    if not prompt_file.exists():
        raise SystemExit(f"Prompt file is missing: {prompt_file}")
    if digest(prompt_file) != expected_prompt:
        raise SystemExit("Prompt hash differs from the recorded run")
    if digest(output) != expected_output:
        raise SystemExit("Generated output hash differs from the recorded run")
    print(json.dumps({"verified": True, "run_id": metrics["run_id"],
                      "prompt_version": metrics["prompt_version"],
                      "model": metrics["model"], "effort": metrics["effort"],
                      "range": metrics["range"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
