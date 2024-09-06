import argparse
from cliapp.core import hello_world

def parse_args(args=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='cliapp CLI')
    parser.add_argument('--name', type=str, help='Name to greet', required=True)
    return parser.parse_args(args)

def main():
    """Main entry point of the CLI."""
    args = parse_args()
    # Call the core function with the parsed argument
    print(hello_world(args.name))

if __name__ == "__main__":
    main()
