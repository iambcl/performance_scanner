import argparse

def main():
    parser = argparse.ArgumentParser(description="Performance Scanner")
    parser.add_subparser()
    parser.add_argument('--name', type=str, help='Your name')
    args = parser.parse_args()

    if args.name:
        print(f"Hello, {args.name}!")
    else:
        print("Hello, World!")