import argparse
import math
import sys
from argparse import ArgumentParser, _SubParsersAction

def _result_filename(value: str) -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise argparse.ArgumentTypeError("expected only a filename, for example ls.json")
    return value

def _add_record(parser: _SubParsersAction):
    record_parser = parser.add_parser("record")
    record_parser.add_argument('--name', type=str, required=True, help='Name of program')
    record_parser.add_argument('--runs', type=_positive_runs, required=True, help='Times to run')
    record_parser.add_argument('command', nargs=argparse.REMAINDER)
    return record_parser

def _positive_runs(value: str) -> int:
    runs = int(value)
    if runs < 1:
        raise argparse.ArgumentTypeError("runs must be at least 1")
    return runs

def _threshold(value: str) -> float:
    threshold = float(value)
    if not math.isfinite(threshold) or threshold < 0:
        raise argparse.ArgumentTypeError("threshold must be finite and nonnegative")
    return threshold

def _add_compare(parser: _SubParsersAction):
    compare_parser = parser.add_parser("compare")
    compare_parser.add_argument('--baseline', type=_result_filename, required=True, help="Filename in results/benchmark (for example ls.json)")
    compare_parser.add_argument('--current', type=_result_filename, required=True, help="Filename in results/readings (for example ls.json)")
    compare_parser.add_argument('--max-time-regression', type=_threshold, default=20, help="Max time regression (default: 20%%)")
    compare_parser.add_argument('--max-memory-regression', type=_threshold, default=20, help="Max memory regression (default: 20%%)")
    return compare_parser

def main():
    parser = argparse.ArgumentParser(description="Performance Scanner")
    subparsers = parser.add_subparsers(dest="action", required=True)
    _add_record(subparsers)
    _add_compare(subparsers)
    args = parser.parse_args()
    if args.action == 'record' and not args.command:
        parser.error("record requires a command")
    if args.action == 'record':
        from src.record_parsing.results import record_action
        try:
            result = record_action(args)
            if result.exit_code != 0:
                raise SystemExit(1)
        except Exception as e:
            print(f"Error while recording results: {e}", file=sys.stderr)
            raise SystemExit(1)
    elif args.action == 'compare':
        from src.compare_results.comparison import compare_results
        try:
            if not all(compare_results(args).values()):
                raise SystemExit(1)
        except Exception as e:
            print(f"Error while comparing results: {e}", file=sys.stderr)
            raise SystemExit(1)

if __name__ == "__main__":
    main()
