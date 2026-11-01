import argparse
from argparse import ArgumentParser, _SubParsersAction

def _add_record(parser: _SubParsersAction):
    record_parser = parser.add_parser("record")
    record_parser.add_argument('--name', type=str, help='Name of program')
    record_parser.add_argument('--runs', type=int, help='Times to run')
    record_parser.add_argument('command', nargs=argparse.REMAINDER)
    return record_parser

def main():
    parser = argparse.ArgumentParser(description="Performance Scanner")
    subparsers = parser.add_subparsers(dest="command")
    parser.add_argument('--name', type=str, help='Your name')
    args = parser.parse_args()

    if args.name:
        print(f"Hello, {args.name}!")
    else:
        print("Hello, World!")