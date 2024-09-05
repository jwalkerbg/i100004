# cliapp/cli.py

import argparse
from cliapp.core import hello_world

def main():
    """Command-line interface for the project."""
    parser = argparse.ArgumentParser(description='MyProject CLI')
    parser.add_argument('--name', type=str, help='Name to greet', required=True)

    args = parser.parse_args()

    # Call the core function from core.py
    print(hello_world(args.name))

if __name__ == "__main__":
    main()
