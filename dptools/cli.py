from dptools import __version__
from importlib import import_module
import argparse

command2module = {
    "input": "dptools.input",
    "parity": "dptools.parity",
    #"run": "dptools.input",
    #"sample": "dptools.sample",
}

class BaseCLI:
    def __init__(self, parser):
        self.parser = parser

    def add_args(self):
        '''Command specific arguments'''
        pass

    def main(self, args):
        '''Command specific main method'''
        pass


def main():
    parser = argparse.ArgumentParser(prog="dptools",
                                     description="DPTools CLI for doing stuff with deepmd-kit",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")
    # TODO: Add logging
    command_clis = {}
    for comm, mod in command2module.items():
        subparser = subparsers.add_parser(comm, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        CLI = import_module(mod).CLI
        cli = CLI(subparser)
        cli.add_args()
        command_clis[comm] = cli

    print(command_clis)
    parsed_args = parser.parse_args()
    command_clis[parsed_args.command].main(parsed_args)
