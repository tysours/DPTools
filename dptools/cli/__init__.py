import argparse
from importlib import import_module
from textwrap import dedent, fill

from dptools import __version__

commands = (
    "input",
    "train",
    "parity",
    "run",
    "sample",
    "convert",
    "set",
    "get",
    "reset",
    "info",
)

class BaseCLI:
    """
    Base class for CLI commands. More or less just a template for reference.

    Args:
        parser (argparse.ArgumentParser): argparse parser for parsing CLI command arguments
    """
    help_info = ""

    def __init__(self, parser):
        self.parser = parser

    def add_args(self):
        '''Command specific arguments'''
        return

    def main(self, args):
        '''Command specific main method'''
        return


class MyFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Simple HelpFormatter that dedents text but retains docstring format"""

    def _fill_text(self, text, width, indent):
        return dedent(text)


def main():
    parser = argparse.ArgumentParser(prog="dptools",
                                     description="DPTools CLI for doing stuff with deepmd-kit\n\n"\
                                             "Complete documentation available at: "\
                                             "https://dptools.rtfd.io",
                                     formatter_class=MyFormatter,
                                     )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")
    # TODO: Add logging
    command_clis = {}
    for comm in commands:
        mod = "dptools.cli." + comm
        CLI = import_module(mod).CLI
        doc = CLI.__doc__
        subparser = subparsers.add_parser(comm, help=CLI.help_info, description=doc,
                formatter_class=MyFormatter)
        cli = CLI(subparser)
        cli.add_args()
        command_clis[comm] = cli

    parsed_args = parser.parse_args()
    command_clis[parsed_args.command].main(parsed_args)
