"""Exercise a selected scanner revision with a fixed recording workload."""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    if not (source / "src/record_parsing/results.py").is_file():
        parser.error(f"scanner source missing from {source}")
    # Load the selected revision while keeping this workload identical for both.
    sys.path.insert(0, str(source))
    from src.record_parsing.results import record_action

    original_directory = Path.cwd()
    with tempfile.TemporaryDirectory() as directory:
        try:
            os.chdir(directory)
            Path("results").mkdir()
            record_action(argparse.Namespace(
                name="workload",
                runs=5,
                command=[sys.executable, "-c", "print(sum(i * i for i in range(1000000)))"],
            ))
            # Read the saved status so older revisions returning None also work.
            result = json.loads(Path("results/workload.json").read_text())
            if result["exit_code"] != 0:
                raise SystemExit(1)
        finally:
            os.chdir(original_directory)


if __name__ == "__main__":
    main()
