from dptools import __version__
from importlib import import_module
import argparse

command2module = {
    "input": "dptools.input",
}


def main():
    parser = argparse.ArgumentParser(prog="dptools",
                                     description="DPTools CLI for doing stuff with deepmd-kit",
                                     )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers()
    # TODO: Add logger
    functions, parsers = {}, {}
    for comm, mod in command2module.items():
        subparser = subparsers.add_parser(comm)
        CLI = import_module(mod).CLI
        cli = CLI(subparser)
        cli.add()

    parsed_args = parser.parse_args()
