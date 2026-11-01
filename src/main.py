import argparse
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path

def _add_record(parser: _SubParsersAction):
    record_parser = parser.add_parser("record")
    record_parser.add_argument('--name', type=str, help='Name of program')
    record_parser.add_argument('--runs', type=int, help='Times to run')
    record_parser.add_argument('command', nargs=argparse.REMAINDER)
    return record_parser

def _add_compare(parser: _SubParsersAction):
    compare_parser = parser.add_parser("compare")
    compare_parser.add_argument('--baseline', type=Path, help="Baseline result to check against")
    compare_parser.add_argument('--current', type=Path, help="Current result to check against")
    compare_parser.add_argument('--max-time-regression', type=Path, help="Max time regression")
    compare_parser.add_argument('--max-memory-regression', type=Path, help="Max memory regression")
    return compare_parser

def main():
    parser = argparse.ArgumentParser(description="Performance Scanner")
    subparsers = parser.add_subparsers(dest="action", required=True)
    _add_record(subparsers)
    _add_compare(subparsers)
    args = parser.parse_args()
    if args.action == 'record':
        from src.record_parsing.results import record_action
        try:
            record_action(args)
        except Exception as e:
            print(f"Error while recording results: {e}")
    elif args.action == 'compare':
        pass

if __name__ == "__main__":
    main()
