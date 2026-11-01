import argparse
from argparse import ArgumentParser, _SubParsersAction

def _result_filename(value: str) -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise argparse.ArgumentTypeError("expected only a filename, for example ls.json")
    return value

def _add_record(parser: _SubParsersAction):
    record_parser = parser.add_parser("record")
    record_parser.add_argument('--name', type=str, help='Name of program')
    record_parser.add_argument('--runs', type=int, help='Times to run')
    record_parser.add_argument('command', nargs=argparse.REMAINDER)
    return record_parser

def _add_compare(parser: _SubParsersAction):
    compare_parser = parser.add_parser("compare")
    compare_parser.add_argument('--baseline', type=_result_filename, required=True, help="Filename in results/benchmark (for example ls.json)")
    compare_parser.add_argument('--current', type=_result_filename, required=True, help="Filename in results/readings (for example ls.json)")
    compare_parser.add_argument('--max-time-regression', type=float, default=20, help="Max time regression (default: 20%%)")
    compare_parser.add_argument('--max-memory-regression', type=float, default=20, help="Max memory regression (default: 20%%)")
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
        from src.compare_results.comparison import compare_results
        try:
            compare_results(args)
        except Exception as e:
            print(f"Error while comparing results: {e}")           

if __name__ == "__main__":
    main()
