"""Unified entry point: python -m tanah <command> [options]."""
import argparse
import importlib
import sys

COMMANDS = {
    'run': 'experiment', 'verify': 'verification', 'coordinates': 'coordinates',
    'audit': 'spatial_audit', 'paper': 'reporting',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=COMMANDS)
    args = parser.parse_args(sys.argv[1:2])
    sys.argv = [f'{sys.argv[0]} {args.command}', *sys.argv[2:]]
    importlib.import_module(f'tanah.{COMMANDS[args.command]}').main()


if __name__ == '__main__':
    main()
